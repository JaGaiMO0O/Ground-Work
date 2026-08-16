#!/usr/bin/env python3
"""init.py - turn this template into your project. Run once.

Picks a profile, fills in the placeholders, applies the profile's scaffold, and
clears away the parts you are not using.

    python scripts/init.py                                  # interactive
    python scripts/init.py --project my-app --profile general \
        --purpose "Ship the new checkout flow" \
        --done "checkout is live and the old flow is deleted"
    python scripts/init.py --dry-run

Read the worked examples under profiles/*/examples/ BEFORE running this - they
are removed at the end, and they are the fastest way to learn the card format.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import _lib as lib
from _lib import ROOT

AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
PROJECT = ROOT / "project.yaml"

PROJECT_TOKEN = "<PROJECT_NAME>"
PURPOSE_RE = re.compile(r"<ONE SENTENCE[^>]*for>")
DONE_RE = re.compile(r"<ONE SENTENCE[^>]*finished>")
DB_ROLE_TOKEN = "<DB_ROLE>"


def available_profiles() -> "list[str]":
    if not lib.PROFILES_DIR.is_dir():
        return []
    return sorted(
        p.name for p in lib.PROFILES_DIR.iterdir()
        if p.is_dir() and not p.name.startswith("_")
    )


def already_initialised() -> bool:
    return PROJECT_TOKEN not in AGENTS.read_text(encoding="utf-8")


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"  {prompt}{suffix}: ").strip()
    except EOFError:
        answer = ""
    return answer or default


def scaffold_files(profile: str) -> "list[Path]":
    root = lib.PROFILES_DIR / profile / "scaffold"
    return [p for p in root.rglob("*") if p.is_file()] if root.is_dir() else []


def apply_scaffold(profile: str) -> "list[str]":
    """Overlay profiles/<profile>/scaffold/** onto the project root."""
    root = lib.PROFILES_DIR / profile / "scaffold"
    written = []
    for source in scaffold_files(profile):
        target = ROOT / source.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        written.append(target.relative_to(ROOT).as_posix())
    return written


GITIGNORE_ADDITIONS = """
# --- added by init.py --adopt ---------------------------------------------
# Working checkout of external code. Reproducible from project.yaml.
systems/
# Secrets. .env.example is committed; .env never is.
.env
!.env.example
# Raw captured traffic is production data - only reduced fixtures are safe.
integration/fixtures/**/raw/
.secrets-baseline.raw.json
"""


def merge_gitignore(target: Path, dry_run: bool) -> str:
    """Append what we need, never rewrite what is there."""
    path = target / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    missing = [
        line for line in ("systems/", ".env", "integration/fixtures/**/raw/")
        if line not in existing
    ]
    if not missing:
        return "already covers what we need"
    if not dry_run:
        path.write_text(existing.rstrip("\n") + "\n" + GITIGNORE_ADDITIONS,
                        encoding="utf-8")
    return f"appended {len(missing)} entry(ies)"


def adopt(args, profile: str) -> int:
    """Bring the scaffold into a repository that already exists."""
    import _adopt

    target = Path(args.adopt).resolve()
    if not target.is_dir():
        return lib.die(f"{target} is not a directory")
    if target == ROOT:
        return lib.die(
            "--adopt needs the OTHER project's directory.\n"
            "     To personalize this template in place, run init.py without --adopt."
        )

    tracked = lib.is_git_repo(target)
    if tracked:
        dirty = lib.git("status", "--porcelain", cwd=target)
        changed = [l for l in dirty.stdout.splitlines() if l.strip()]
        if changed and not args.force:
            lib.err(f"{target.name} has {len(changed)} uncommitted change(s)")
            lib.info(
                "       Commit or stash first, so `git diff` afterwards shows\n"
                "       exactly what adoption did and nothing else.\n"
                "       Or re-run with --force."
            )
            return 1
    elif not args.force:
        # Refusing, not warning. Adoption writes ~80 files; in a git repo that
        # is undoable in one command, and without one it is an afternoon of
        # deleting things by hand. The advice this tool gives elsewhere assumes
        # an undo exists, so it should not proceed where none does.
        lib.err(f"{target.name} is not a git repository - adoption has no undo")
        lib.info(
            "       Adoption adds dozens of files. Under git, removing them is\n"
            "       one command; without it, there is no way back.\n"
            "       Run `git init` there first - that is the real fix, and it is\n"
            "       worth having anyway. Or copy the project somewhere safe and\n"
            "       adopt the copy. Or re-run with --force and accept the risk."
        )
        return 1
    else:
        lib.warn(f"{target.name} is not a git repository - no undo, and churn "
                 "ranking is unavailable")

    found = _adopt.detect(target)
    areas = _adopt.propose_areas(target)
    name = args.project or target.name.lower().replace(" ", "-")

    lib.info(f"\n  adopting {target}")
    lib.info(f"  profile   {profile}"
             + ("" if args.keep_profiles else "   (the others are not copied)"))
    lib.info(f"  stack     {', '.join(f'{k}={v}' for k, v in found.stack.items()) or 'not recognised'}")
    lib.info(f"  commands  {', '.join(found.commands) or 'none detected'}"
             + (f"   (from {', '.join(found.sources)})" if found.sources else ""))
    lib.info(f"  areas     {', '.join(a[0] for a in areas) or 'none proposed'}")

    plan = _adopt.scaffold_plan(ROOT, target, profile, args.keep_profiles)
    counts = _adopt.apply_plan(plan, args.dry_run)

    generated = [
        (target / "project.yaml", _adopt.project_yaml(name, profile, found, areas)),
        (target / "RUNBOOK.md", _adopt.runbook(name, found)),
    ]
    status_src = ROOT / "STATUS.md"
    if status_src.is_file():
        from datetime import date

        text = status_src.read_text(encoding="utf-8").replace(
            "reviewed: <date>", f"reviewed: {date.today().isoformat()}"
        )
        generated.append((target / "STATUS.md", text))

    lib.info("")
    for path, text in generated:
        verb = "would write" if args.dry_run else "wrote"
        if path.exists():
            final = path.with_suffix(path.suffix + ".proposed")
            note = f"{verb} {final.name} ({path.name} already exists)"
        else:
            final = path
            note = f"{verb} {path.name}"
        if not args.dry_run:
            final.write_text(text, encoding="utf-8")
        lib.ok(note)

    lib.ok(f".gitignore: {merge_gitignore(target, args.dry_run)}")

    if not args.dry_run:
        # Generate the search surface now, so the very first grep in the adopted
        # project already excludes noise and credential-bearing files.
        subprocess.run(
            [sys.executable, str(target / "scripts" / "sync.py"), "--rgignore-only"],
            cwd=str(target), capture_output=True,
        )
        lib.ok(".rgignore generated from the detected areas")
    lib.ok(f"scaffold: {counts['add']} added, {counts['proposed']} proposed "
           f"alongside existing files, {counts['skip']} already present")

    if args.dry_run:
        lib.info("\n  dry run - nothing was written\n")
        return 0

    proposed = [d for _s, d, a in plan if a == "proposed"]
    if proposed:
        lib.info("\n  These already existed, so ours are alongside as .proposed:")
        for path in proposed[:8]:
            lib.info(f"       {path.relative_to(target).as_posix()}.proposed")
        lib.info("       Merge what you want and delete the rest. Nothing was "
                 "overwritten.")

    if tracked:
        lib.info(
            "\n  If you want out: `git clean -nd` lists everything adoption\n"
            "  added, and `git clean -fd` removes it. That is exact only "
            "because\n  the tree was clean before this ran."
        )

    lib.info(
        "\n  Next, in " + target.name + ":\n"
        "    1. project.yaml  - fix the proposed areas; they are a guess\n"
        "    2. RUNBOOK.md    - verify the detected commands actually run\n"
        "    3. python scripts/scan.py\n"
        "    4. python scripts/usage.py    - see what this project has cost so far\n"
        "\n  Then pick the busiest area and write its card.\n"
    )

    lib.info("  Validating the result...\n")
    code = subprocess.run(
        [sys.executable, str(target / "scripts" / "check.py")], cwd=str(target)
    ).returncode
    return 1 if code == 1 else 0


def main() -> int:
    profiles = available_profiles()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--adopt", metavar="DIR",
                        help="bring the scaffold into an existing project")
    parser.add_argument("--project")
    parser.add_argument("--profile", choices=profiles or None)
    parser.add_argument("--purpose")
    parser.add_argument("--done")
    parser.add_argument("--db-role", default="analyst_ro")
    parser.add_argument("--keep-examples", action="store_true",
                        help="do not delete the worked examples")
    parser.add_argument("--keep-profiles", action="store_true",
                        help="keep the profiles you are not using (with --adopt, "
                             "copy them across too)")
    parser.add_argument("--git", action="store_true", help="run git init")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="re-run even though this project looks initialised")
    args = parser.parse_args()

    if not AGENTS.exists():
        return lib.die("AGENTS.md not found - run this from the project root")
    if not profiles:
        return lib.die("no profiles/ directory - the template is incomplete")

    if args.adopt:
        return adopt(args, args.profile or "general")

    if already_initialised() and not args.force:
        lib.warn("this project looks initialised already (no placeholders in AGENTS.md)")
        lib.info("       Re-run with --force if you really mean it.")
        return 0

    project = args.project
    profile = args.profile
    purpose = args.purpose
    done = args.done
    db_role = args.db_role

    interactive = not all([project, profile, purpose, done])
    if interactive:
        if not sys.stdin.isatty():
            return lib.die(
                "not a terminal - pass --project, --profile, --purpose and --done"
            )
        lib.info(
            "\n  A few questions. The answers go into AGENTS.md, which is loaded on\n"
            "  every single turn of every conversation - so keep them to one line.\n"
        )
        project = project or ask("Project name", ROOT.name.lower().replace(" ", "-"))
        if not profile:
            lib.info(f"\n  Profiles: {', '.join(profiles)}")
            lib.info("  'general' is right for almost everything. See profiles/README.md.")
            profile = ask("Profile", "general")
            while profile not in profiles:
                lib.warn(f"unknown profile {profile!r}")
                profile = ask("Profile", "general")
        purpose = purpose or ask("Purpose (one sentence)")
        done = done or ask("Done = (one sentence)")

    profile = profile or "general"
    if not purpose or not done:
        return lib.die(
            "purpose and done are required - they are what keeps scope honest"
        )

    edits = []
    agents_text = AGENTS.read_text(encoding="utf-8")
    agents_text = agents_text.replace(PROJECT_TOKEN, project)
    agents_text = PURPOSE_RE.sub(purpose, agents_text)
    agents_text = DONE_RE.sub(done, agents_text)
    agents_text = agents_text.replace(DB_ROLE_TOKEN, db_role or "none")
    edits.append((AGENTS, agents_text))

    edits.append((README, README.read_text(encoding="utf-8")
                  .replace(PROJECT_TOKEN, project)))

    project_text = PROJECT.read_text(encoding="utf-8").replace(PROJECT_TOKEN, project)
    project_text = re.sub(r"^profile:.*$", f"profile: {profile}",
                          project_text, count=1, flags=re.M)
    edits.append((PROJECT, project_text))

    # The purpose and done answers ARE the goal ladder. Ask once, fill both.
    status_path = ROOT / "STATUS.md"
    if status_path.exists():
        from datetime import date

        status_text = status_path.read_text(encoding="utf-8")
        status_text = status_text.replace(
            "reviewed: <date>", f"reviewed: {date.today().isoformat()}"
        )
        status_text = status_text.replace(
            "<what this phase is for, in one line>", purpose
        )
        status_text = status_text.replace(
            "<the condition that ends this phase - be specific enough to "
            "disagree with>",
            done,
        )
        edits.append((status_path, status_text))

    unused = [p for p in profiles if p != profile]
    example_dirs = [
        d for p in profiles
        for d in [lib.PROFILES_DIR / p / "examples"]
        if d.is_dir()
    ]

    if args.dry_run:
        lib.info("\n  dry run - nothing written\n")
        lib.info(f"       profile: {profile}")
        for path, _ in edits:
            lib.info(f"       would rewrite {path.relative_to(ROOT).as_posix()}")
        for name in scaffold_files(profile):
            target = (ROOT / name.relative_to(lib.PROFILES_DIR / profile / "scaffold"))
            lib.info(f"       would add     {target.relative_to(ROOT).as_posix()}")
        if not args.keep_examples:
            for d in example_dirs:
                lib.info(f"       would delete  {d.relative_to(ROOT).as_posix()}/")
        if not args.keep_profiles and unused:
            lib.info(f"       would delete  unused profiles: {', '.join(unused)}")
        if args.git:
            lib.info("       would run git init")
        return 0

    for path, text in edits:
        path.write_text(text, encoding="utf-8")
        lib.ok(f"personalized {path.relative_to(ROOT).as_posix()}")

    written = apply_scaffold(profile)
    if written:
        lib.ok(f"applied the {profile} scaffold ({len(written)} files)")
        for name in written[:6]:
            lib.info(f"       {name}")
        if len(written) > 6:
            lib.info(f"       ... and {len(written) - 6} more")

    if not args.keep_examples:
        for d in example_dirs:
            shutil.rmtree(d, ignore_errors=True)
        if example_dirs:
            lib.ok("removed the worked examples")

    if not args.keep_profiles and unused:
        for name in unused:
            shutil.rmtree(lib.PROFILES_DIR / name, ignore_errors=True)
        lib.ok(f"removed unused profile(s): {', '.join(unused)}")
        lib.info("       To switch profiles later, copy the directory back from "
                 "the template.")

    # The scaffold is now part of the project, not a pending overlay.
    scaffold_root = lib.PROFILES_DIR / profile / "scaffold"
    if scaffold_root.is_dir():
        shutil.rmtree(scaffold_root, ignore_errors=True)

    if args.git:
        if lib.is_git_repo():
            lib.ok("already a git repository")
        else:
            result = lib.git("init", "-q")
            if result.returncode == 0:
                lib.ok("git init")
            else:
                lib.warn(f"git init failed: {result.stderr.strip()}")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "sync.py"),
                    "--rgignore-only"], cwd=str(ROOT))

    lib.info(
        "\n  Next, in order:\n"
        "    1. edit project.yaml       - declare your areas and commands\n"
        "    2. edit RUNBOOK.md         - how to build, test and run this\n"
        "    3. python scripts/scan.py  - the secret gate, before an agent reads anything\n"
        "    4. python scripts/new_card.py <area>   - then survey it\n"
        "\n  Lost? Read START-HERE.md.\n"
    )
    lib.info("  Validating the result...\n")
    code = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check.py")], cwd=str(ROOT)
    ).returncode
    # check.py exits 2 for warnings-only. init itself still succeeded, so only a
    # hard validation error should fail this command.
    return 1 if code == 1 else 0


if __name__ == "__main__":
    sys.exit(main())
