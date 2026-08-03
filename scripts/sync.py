#!/usr/bin/env python3
"""sync.py - build systems/ from project.yaml, and regenerate .rgignore.

Checks out each declared repo at its PINNED ref, fetching only the paths named
in `sparse:`. Everything else never lands on disk, which is the cheapest token
lever available: an agent cannot wander into code that was never fetched.

systems/ is disposable. Delete it and re-run this at any time.

    python scripts/sync.py                # everything
    python scripts/sync.py --only billing-legacy
    python scripts/sync.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import _lib as lib
from _lib import ROOT


def _sparse_patterns(area: lib.Area) -> "list[str]":
    return [str(p) for p in area.sparse]


def _apply_sparse(dest: Path, patterns: "list[str]") -> None:
    """Prefer the modern porcelain; fall back to the info/sparse-checkout file
    so this still works on the older git a legacy shop is likely to have."""
    if not patterns:
        lib.git("sparse-checkout", "disable", cwd=dest)
        return

    result = lib.git("sparse-checkout", "set", "--no-cone", *patterns, cwd=dest)
    if result.returncode == 0:
        return

    lib.git("config", "core.sparseCheckout", "true", cwd=dest)
    info_dir = dest / ".git" / "info"
    info_dir.mkdir(parents=True, exist_ok=True)
    (info_dir / "sparse-checkout").write_text(
        "\n".join(patterns) + "\n", encoding="utf-8"
    )


def sync_repo(area: lib.Area, dry_run: bool) -> "tuple[bool, str]":
    """-> (ok, detail). Never raises; the caller reports."""
    dest = area.checkout
    patterns = _sparse_patterns(area)

    if dry_run:
        scope = f"{len(patterns)} sparse path(s)" if patterns else "FULL repo"
        return True, f"would fetch {area.url} @ {area.ref} ({scope})"

    if not (dest / ".git").exists():
        dest.mkdir(parents=True, exist_ok=True)
        init = lib.git("init", "-q", cwd=dest)
        if init.returncode != 0:
            return False, f"git init failed: {init.stderr.strip()}"
        lib.git("remote", "add", "origin", area.url or "", cwd=dest)
    else:
        lib.git("remote", "set-url", "origin", area.url or "", cwd=dest)

    _apply_sparse(dest, patterns)

    # Shallow-fetch the pinned ref. Fetching a bare SHA needs server support, so
    # fall back to a full fetch rather than failing the sync.
    ref = area.ref or "HEAD"
    fetch = lib.git("fetch", "--depth", "1", "origin", ref, cwd=dest)
    target = "FETCH_HEAD"
    if fetch.returncode != 0:
        deep = lib.git("fetch", "--tags", "origin", cwd=dest)
        if deep.returncode != 0:
            return False, f"fetch failed: {fetch.stderr.strip().splitlines()[-1:]}"
        resolved = lib.git("rev-parse", "--verify", f"{ref}^{{commit}}", cwd=dest)
        if resolved.returncode != 0:
            resolved = lib.git("rev-parse", "--verify", f"origin/{ref}", cwd=dest)
        if resolved.returncode != 0:
            return False, f"ref {ref!r} not found on the remote"
        target = resolved.stdout.strip()

    checkout = lib.git("checkout", "--detach", "--force", target, cwd=dest)
    if checkout.returncode != 0:
        return False, f"checkout failed: {checkout.stderr.strip()}"

    sha = lib.git("rev-parse", "HEAD", cwd=dest).stdout.strip()[:9]
    # Count what is actually materialized, not index entries -- under sparse
    # checkout the index still lists every path in the repo, which would
    # overstate the search surface by an order of magnitude.
    on_disk = sum(
        1 for p in dest.rglob("*") if p.is_file() and ".git" not in p.parts
    )
    return True, f"{sha}  {on_disk} file(s) on disk"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", metavar="AREA", help="sync just this area")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--rgignore-only",
        action="store_true",
        help="regenerate .rgignore and skip every checkout - touches no network",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="delete checkouts under systems/ that are no longer declared",
    )
    args = parser.parse_args()

    project = lib.load_project()
    if project.errors:
        for problem in project.errors:
            lib.err(problem)
        return lib.die("project.yaml has schema errors; fix them first")

    if args.rgignore_only:
        targets: list = []
    elif args.only:
        targets = [project.require(args.only)]
    else:
        targets = project.areas
    failures = 0
    state: dict = {}

    for area in targets:
        if not area.clonable:
            lib.info(f"  {area.name:24} skipped - kind: {area.kind}, nothing to clone")
            continue

        good, detail = sync_repo(area, args.dry_run)
        if good:
            lib.ok(f"{area.name:24} {detail}")
            state[area.name] = {"ref": area.ref, "detail": detail}
        else:
            lib.err(f"{area.name:24} {detail}")
            failures += 1

    if args.prune and not args.dry_run:
        declared = {s.name for s in project.areas}
        systems_dir = ROOT / "systems"
        if systems_dir.exists():
            for path in systems_dir.iterdir():
                if path.is_dir() and path.name not in declared:
                    shutil.rmtree(path, ignore_errors=True)
                    lib.warn(f"pruned systems/{path.name} (no longer declared)")

    if not args.dry_run:
        (ROOT / ".rgignore").write_text(lib.rgignore_text(project), encoding="utf-8")
        lib.ok(".rgignore regenerated from project.yaml")

        systems_dir = ROOT / "systems"
        systems_dir.mkdir(exist_ok=True)
        (systems_dir / ".sync-state.json").write_text(
            json.dumps(state, indent=2) + "\n", encoding="utf-8"
        )

    if failures:
        lib.err(f"{failures} area(s) failed to sync")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
