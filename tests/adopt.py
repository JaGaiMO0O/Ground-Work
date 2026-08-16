"""Prove `init.py --adopt` is safe on a project that already exists.

    python tests/adopt.py
    python tests/adopt.py --only profile

Adoption is the only thing in this repo that writes into somebody else's
project, and it had no test until three defects were found by hand in a real
one. Each of the cases below is one of those defects, or one of the promises
`_adopt.py` makes in its docstring:

  * never clobber - a file that already exists is left alone
  * refuse where there is no undo - a dirty tree, or no git at all
  * carry only what the project will use - one profile, not all of them

Mechanics follow tests/invariants.py: work dirs OUTSIDE the repo, because a
lingering git process holds an open handle and rmtree fails mid-run on Windows.
The template is this repo, read in place - adoption only ever reads from it, so
there is nothing to copy first.
"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = Path(tempfile.gettempdir()) / "adopt-harness"

LEGACY_PROFILE = "legacy-modernization"


def nuke(path: Path):
    """git packs objects read-only, which defeats plain rmtree on Windows."""

    def force(func, target, _exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass

    for _ in range(4):
        if not path.exists():
            return
        try:
            shutil.rmtree(path, onexc=force)
        except OSError:
            time.sleep(0.3)


def git(target: Path, *args: str):
    return subprocess.run(["git", *args], cwd=str(target),
                          capture_output=True, text=True)


def inventory(target: Path) -> dict:
    """Every file outside .git, with its bytes. The 'nothing was touched'
    assertion has to see content, not just names - a rewritten README keeps its
    name."""
    found = {}
    for path in target.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            found[path.relative_to(target).as_posix()] = path.read_bytes()
        except OSError:
            pass
    return found


# --- fixtures --------------------------------------------------------------


def make(index: int, *, use_git: bool, commit: bool = True,
         extra: "dict[str, str] | None" = None) -> Path:
    """A small python project, shaped like the one the first trial ran on:
    a multi-file src/ and a single-file app/."""
    target = BASE / f"case-{index:02d}"
    nuke(target)
    files = {
        "src/train.py": "print('train')\n",
        "src/preprocess.py": "print('prep')\n",
        "app/app.py": "print('serve')\n",
        "requirements.txt": "flask\n",
        "README.md": "# toy\n",
    }
    files.update(extra or {})
    for rel, text in files.items():
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    if use_git:
        git(target, "init", "-q")
        git(target, "config", "user.email", "t@t")
        git(target, "config", "user.name", "t")
        git(target, "config", "gc.auto", "0")
        if commit:
            git(target, "add", "-A")
            git(target, "commit", "-qm", "base")
    return target


def build_plain(i):
    return make(i, use_git=False)


def build_git(i):
    return make(i, use_git=True)


def build_dirty(i):
    target = make(i, use_git=True)
    (target / "src" / "train.py").write_text("print('edited')\n", encoding="utf-8")
    return target


def build_with_agents(i):
    return make(i, use_git=True, extra={"AGENTS.md": "# their router\nMine.\n"})


def build_with_gitignore(i):
    return make(i, use_git=True, extra={".gitignore": "*.pyc\n"})


# --- assertions ------------------------------------------------------------
# Each returns "" for pass, or a sentence naming what was wrong.


def untouched(target, before, after, _out):
    if before == after:
        return ""
    added = sorted(set(after) - set(before))
    return f"{len(added)} file(s) were written, e.g. {added[:3]}"


def scaffold_arrived(target, _before, after, _out):
    for wanted in ("AGENTS.md", "project.yaml", "RUNBOOK.md", "STATUS.md",
                   "scripts/check.py"):
        if wanted not in after:
            return f"{wanted} was not written"
    return ""


def nothing_modified(target, before, after, _out):
    """The promise the whole design rests on: adoption adds, it never edits."""
    changed = [k for k in before if k in after and before[k] != after[k]]
    if changed:
        return f"modified pre-existing file(s): {changed}"
    if not set(after) - set(before):
        return "nothing was added at all"
    return ""


def agents_preserved(target, before, after, _out):
    if after.get("AGENTS.md") != before.get("AGENTS.md"):
        return "their AGENTS.md was overwritten"
    if "AGENTS.md.proposed" not in after:
        return "ours did not land alongside as AGENTS.md.proposed"
    return ""


def gitignore_appended(target, before, after, _out):
    old = before[".gitignore"].decode()
    new = after[".gitignore"].decode()
    if not new.startswith(old.rstrip("\n")):
        return "their .gitignore was rewritten rather than appended to"
    if ".env" not in new:
        return "our entries were not appended"
    return ""


def one_profile_only(target, _before, after, _out):
    profiles = {k.split("/")[1] for k in after
                if k.startswith("profiles/") and k.count("/") >= 2}
    if LEGACY_PROFILE in profiles:
        return f"the unused profile travelled: {sorted(profiles)}"
    return ""


def all_profiles(target, _before, after, _out):
    profiles = {k.split("/")[1] for k in after
                if k.startswith("profiles/") and k.count("/") >= 2}
    if LEGACY_PROFILE not in profiles:
        return "--keep-profiles did not keep them"
    return ""


def legacy_overlay(target, _before, after, _out):
    """A profile's scaffold is an overlay. Landing it under profiles/ puts the
    templates somewhere no rule and no reader looks."""
    for wanted in ("integration/strangler-plan.md", "map/_TEMPLATE/seams.md",
                   "context/recipes/survey-system.md"):
        if wanted not in after:
            return f"{wanted} did not reach the project root"
    stranded = [k for k in after if "/scaffold/" in k]
    if stranded:
        return f"the scaffold was also left under profiles/: {stranded[:2]}"
    return ""


def carries_only_what_runs(target, _before, after, _out):
    """ADR 0003: copying rather than installing is only defensible if it copies
    what the project will actually invoke."""
    for unwanted, why in (
        ("tests/", "the scaffold's own tests"),
        ("scripts/init.py", "the adoption tool, after adoption"),
        ("scripts/_adopt.py", "the adoption tool, after adoption"),
        ("scripts/check.sh", "a shell alias for check.py"),
        ("scripts/check.ps1", "a shell alias for check.py"),
    ):
        hit = [k for k in after if k == unwanted or k.startswith(unwanted)]
        if hit:
            return f"copied {why}: {hit[:2]}"
    for wanted in ("scripts/check.py", "scripts/hooks/guard.py",
                   "scripts/adapters/db/_stub.sh", "docs/adapters.md"):
        if wanted not in after:
            return f"{wanted} should have travelled and did not"
    return ""


def app_is_an_area(target, _before, after, _out):
    """One file is enough to be an area. Requiring two silently dropped the
    single-file serving layer that every session was reading."""
    text = after.get("project.yaml", b"").decode(errors="replace")
    if "name: app" not in text:
        return "the single-file app/ directory was not proposed as an area"
    if "name: src" not in text:
        return "src/ was not proposed as an area"
    return ""


#  name                                build             extra argv                  exit  assertion
CASES = [
    ("no git -> refuses",               build_plain,      [],                          1, untouched),
    ("no git + --force -> adopts",      build_plain,      ["--force"],                 0, scaffold_arrived),
    ("dirty tree -> refuses",           build_dirty,      [],                          1, untouched),
    ("--dry-run writes nothing",        build_git,        ["--dry-run"],               0, untouched),
    ("clean tree -> adopts",            build_git,        [],                          0, scaffold_arrived),
    ("adds, never edits          [+]",  build_git,        [],                          0, nothing_modified),
    ("their AGENTS.md survives   [+]",  build_with_agents, [],                         0, agents_preserved),
    (".gitignore appended, not cut",    build_with_gitignore, [],                      0, gitignore_appended),
    ("only the chosen profile",         build_git,        [],                          0, one_profile_only),
    ("--keep-profiles keeps them [+]",  build_git,        ["--keep-profiles"],         0, all_profiles),
    ("legacy scaffold reaches root",    build_git,        ["--profile", LEGACY_PROFILE], 0, legacy_overlay),
    ("one-file directory is an area",   build_git,        [],                          0, app_is_an_area),
    ("carries only what it runs",       build_git,        [],                          0, carries_only_what_runs),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", help="run only cases whose name contains this")
    parser.add_argument("--keep", action="store_true", help="leave work dirs behind")
    args = parser.parse_args()

    cases = [c for c in CASES if not args.only or args.only.lower() in c[0].lower()]
    if not cases:
        print(f"no case matches {args.only!r}")
        return 1

    nuke(BASE)
    BASE.mkdir(parents=True, exist_ok=True)
    failures = 0
    started = time.time()

    print(f"{'case':36} {'exit':>4} {'want':>4}  result", flush=True)
    print("-" * 76, flush=True)
    for index, (name, build, argv, want_code, assertion) in enumerate(cases):
        target = build(index)
        before = inventory(target)
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "init.py"),
             "--adopt", str(target), *argv],
            cwd=str(target), capture_output=True, text=True,
        )
        after = inventory(target)
        output = proc.stdout + proc.stderr
        problem = assertion(target, before, after, output)
        code_ok = proc.returncode == want_code
        good = code_ok and not problem
        failures += 0 if good else 1
        note = "ok" if good else ("WRONG EXIT" if not code_ok else problem)
        print(f"{name:36} {proc.returncode:>4} {want_code:>4}  {note}", flush=True)
        if not good:
            print("   ---- output ----", flush=True)
            for line in output.strip().splitlines()[:16]:
                print("   " + line, flush=True)

    if not args.keep:
        nuke(BASE)
    print("-" * 76, flush=True)
    print(
        f"{len(cases) - failures}/{len(cases)} passed in {time.time() - started:.0f}s"
        "   ([+] = positive control)",
        flush=True,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
