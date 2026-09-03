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
  * carry TEMPLATES, never content - no dated handoff, ADR or goal ladder of
    ours reaches somebody else's repository
  * say true things - the personalized router, and an undo that names what it
    does not cover

Mechanics follow tests/invariants.py: work dirs OUTSIDE the repo, because a
lingering git process holds an open handle and rmtree fails mid-run on Windows.
The template is this repo, read in place - adoption only ever reads from it, so
there is nothing to copy first.
"""

from __future__ import annotations

import argparse
import json
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

# Adoption leaves Tier 0 unfilled unless it is told what the project is for, and
# check.py now fails on an unfilled Tier 0 - so every case that expects a clean
# exit has to answer the two questions. One case deliberately does not, and
# expects the failure.
FILLED = ["--purpose", "score names against a watchlist",
          "--done", "the new screen is live and the old one is deleted"]


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


# Path set per fixture, captured before adoption. Directories included, and
# that is the point: the old undo deleted three empty ones that predated it,
# and `git status --porcelain` cannot see an untracked empty directory, so
# nothing in the git state revealed the loss.
SNAPSHOTS = {}


def paths_of(target: Path) -> "set[str]":
    found = set()
    for path in target.rglob("*"):
        if ".git" in path.parts:
            continue
        found.add(path.relative_to(target).as_posix() + ("/" if path.is_dir() else ""))
    return found


def run_init(target: Path, *argv):
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / "init.py"), *argv],
        cwd=str(target), capture_output=True, text=True,
    )


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
    SNAPSHOTS[str(target)] = paths_of(target)
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


def build_undo_target(i):
    """The JLGC shape: a gitignored `.claude/`, and empty directories that
    predate adoption. Those two are what made the old undo wrong in both
    directions - it left 8 files behind and deleted 3 directories it had never
    written."""
    target = make(i, use_git=True, extra={".gitignore": "*.pyc\n.claude/\n"})
    (target / "emptydir").mkdir(exist_ok=True)
    (target / ".cursor").mkdir(exist_ok=True)
    SNAPSHOTS[str(target)] = paths_of(target)
    return target


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


def no_template_only_files_travel(target, _before, after, _out):
    """LICENSE, TESTING.md and .gitlab/ describe the TEMPLATE, not a project
    made from it.

    LICENSE is the one with teeth: it is Optimiza's licence over the scaffold,
    so copying it into somebody's repository would put that notice over their
    own work - and its own text says a scaffolded project is theirs. The other
    two would send the adopter a testing brief for a build they are not
    testing.
    """
    for unwanted, why in (
        ("LICENSE", "the scaffold's licence, over the adopter's own work"),
        ("TESTING.md", "a testing brief for the scaffold, not their project"),
        (".gitlab/", "issue templates pointing at somebody else's tracker"),
    ):
        hit = [k for k in after if k == unwanted or k.startswith(unwanted)]
        if hit:
            return f"copied {why}: {hit[:2]}"
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


def no_live_content(target, _before, after, _out):
    """Rule 4, and the worst of the three defects the Name Screening adoption
    found: the scaffold shipped its own state as the project's. AGENTS.md routes
    to STATUS.md for 'where this project stands' and to the newest handoff for
    'what happened last session', so the first two files an agent read there
    described Ground Work - confidently, in the always-loaded tier."""
    for folder, what in (("context/handoffs/", "handoffs"),
                         ("docs/decisions/", "decisions")):
        live = [k for k in after
                if k.startswith(folder) and not k.rsplit("/", 1)[1].startswith("_")]
        if live:
            return f"non-template {what} travelled: {sorted(live)[:3]}"
    for wanted in ("context/handoffs/_TEMPLATE.md", "docs/decisions/_TEMPLATE.md"):
        if wanted not in after:
            return f"{wanted} should have travelled and did not"

    status = after.get("STATUS.md", b"").decode(errors="replace")
    if "## Goal ladder" not in status or "## Blockers" not in status:
        return "STATUS.md did not arrive, or is not the template"
    # Every blocker this repo has ever recorded carries this name, and the goal
    # ladder names the repo. Either in a stranger's STATUS.md is the defect.
    for leak in ("myaghmour", "Ground Work", "Legacy Modernization"):
        if leak in status:
            return f"STATUS.md arrived carrying our own state ({leak!r})"
    return ""


def agents_personalized(target, _before, after, _out):
    """Plain init.py has always substituted these; adopt() never had. An adopted
    project's router opened `# Project: <PROJECT_NAME>`, and check.py measured
    its token budget and called it fine."""
    text = after.get("AGENTS.md", b"").decode(errors="replace")
    left = [t for t in ("<PROJECT_NAME>", "<ONE SENTENCE", "<DB_ROLE>") if t in text]
    if left:
        return f"Tier 0 arrived unfilled: {left}"
    if f"# Project: {target.name}" not in text:
        return "the project name did not reach the router"
    if "score names against a watchlist" not in text:
        return "--purpose did not reach the router"
    return ""


def unfilled_tier0_fails(target, _before, after, out):
    """The other half of defect 2: with nothing to fill them in with, the blanks
    have to survive AND be loud. Silence was the bug."""
    text = after.get("AGENTS.md", b"").decode(errors="replace")
    if "<ONE SENTENCE" not in text:
        return "the blanks were filled from somewhere - rule 2 says do not invent"
    if "template placeholders" not in out:
        return "check.py stayed silent about an unfilled router"
    return ""


def undo_is_honest(target, _before, after, out):
    """The message must offer the real undo and say why `git clean` is not it -
    and the reason must be ASKED of this project, not recited from ours."""
    if "--undo" not in out:
        return "no undo was offered at all"
    if ".adopt-manifest.json" not in after:
        return "no manifest was written, so there is nothing to undo from"
    if "gitignores" not in out:
        return "does not say git clean skips the files THIS project ignores"
    if "Nor would it restore .gitignore" not in out:
        return "does not say .gitignore was MODIFIED, which git clean cannot undo"
    if not (target / "systems" / ".sync-state.json").is_file():
        return "fixture drift: sync.py no longer writes systems/.sync-state.json"
    if ".sync-state.json" not in out:
        return "systems/.sync-state.json was written and never reported"
    manifest = json.loads(after[".adopt-manifest.json"].decode())
    if "systems/.sync-state.json" not in manifest["files"]:
        return "the manifest omits a file adoption wrote, so the undo will miss it"
    # Found by running the undo instead of reading it. This project ignores
    # *.pyc, so a __pycache__ we left behind is ignored too, and `git clean -fd`
    # walks straight past it - a third thing the message did not cover.
    cached = [k for k in after if "__pycache__" in k]
    if cached:
        return f"left bytecode behind, which git clean -fd skips: {cached[:2]}"
    return ""


def undo_omits_the_gitignore_caveat(target, before, after, out):
    """Positive control on the branch above. With no .gitignore of their own,
    adoption CREATED one - so it is an added file the undo simply deletes, and
    claiming it must be restored would be the same class of wrong."""
    if ".gitignore" in before:
        return "fixture error: this case needs a project with no .gitignore"
    if "Nor would it restore .gitignore" in out:
        return "promises to restore a .gitignore adoption created, not modified"
    manifest = json.loads(after[".adopt-manifest.json"].decode())
    if manifest.get("gitignore_appended") is not None:
        return "recorded prior .gitignore bytes for a file that did not exist"
    if ".gitignore" not in manifest["files"]:
        return "adoption created .gitignore and did not record it as added"
    return ""


def undo_is_exact(target, before, after, _out):
    """The pass condition the JLGC trial set: the after-undo state equals the
    before state. Files, directories, and bytes."""
    expected = SNAPSHOTS[str(target)]
    if paths_of(target) == expected:
        return "adoption wrote nothing, so the undo would prove nothing"
    result = run_init(target, "--undo", str(target))
    if result.returncode != 0:
        return "undo exited %d" % result.returncode
    now = paths_of(target)
    if now != expected:
        eaten = sorted(expected - now)
        if eaten:
            return "deleted what it never wrote: %s" % eaten[:3]
        return "left behind: %s" % sorted(now - expected)[:3]
    after_undo = inventory(target)
    changed = [k for k, v in before.items() if after_undo.get(k) != v]
    if changed:
        return "restored, but not byte-for-byte: %s" % changed
    return ""


def undo_keeps_edited_files(target, _before, _after, _out):
    """Once you have edited a file adoption wrote, it is your file."""
    mine = target / "AGENTS.md"
    if not mine.is_file():
        return "fixture drift: adoption did not write AGENTS.md"
    mine.write_text("# my own router\n", encoding="utf-8")
    result = run_init(target, "--undo", str(target))
    if result.returncode != 0:
        return "undo exited %d" % result.returncode
    if not mine.is_file():
        return "deleted a file that had been edited since adoption"
    if mine.read_text(encoding="utf-8") != "# my own router\n":
        return "kept the file but changed it"
    if not (target / ".adopt-manifest.json").is_file():
        return "removed the manifest, the only record of what it kept and why"
    return ""


def undo_refuses_without_manifest(target, _before, _after, _out):
    """No record, no guessing. Deleting by pattern is how you eat somebody's
    own AGENTS.md."""
    before = paths_of(target)
    result = run_init(target, "--undo", str(target))
    if result.returncode == 0:
        return "undid something with no manifest to undo it from"
    if "nothing to" not in (result.stdout + result.stderr):
        return "refused without saying why"
    if paths_of(target) != before:
        return "refused and still changed the tree"
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


#  name                                build             extra argv                            exit  assertion
CASES = [
    ("no git -> refuses",               build_plain,      FILLED,                                1, untouched),
    ("no git + --force -> adopts",      build_plain,      FILLED + ["--force"],                  0, scaffold_arrived),
    ("dirty tree -> refuses",           build_dirty,      FILLED,                                1, untouched),
    ("--dry-run writes nothing",        build_git,        FILLED + ["--dry-run"],                0, untouched),
    ("clean tree -> adopts",            build_git,        FILLED,                                0, scaffold_arrived),
    ("adds, never edits          [+]",  build_git,        FILLED,                                0, nothing_modified),
    ("their AGENTS.md survives   [+]",  build_with_agents, FILLED,                               0, agents_preserved),
    (".gitignore appended, not cut",    build_with_gitignore, FILLED,                            0, gitignore_appended),
    ("only the chosen profile",         build_git,        FILLED,                                0, one_profile_only),
    ("--keep-profiles keeps them [+]",  build_git,        FILLED + ["--keep-profiles"],          0, all_profiles),
    ("legacy scaffold reaches root",    build_git,        FILLED + ["--profile", LEGACY_PROFILE], 0, legacy_overlay),
    ("one-file directory is an area",   build_git,        FILLED,                                0, app_is_an_area),
    ("carries only what it runs",       build_git,        FILLED,                                0, carries_only_what_runs),
    ("no template-only files travel",   build_git,        FILLED,                                0, no_template_only_files_travel),
    # the three defects the Name Screening adoption found
    ("no live content travels",         build_git,        FILLED,                                0, no_live_content),
    ("router arrives personalized",     build_git,        FILLED,                                0, agents_personalized),
    ("unfilled Tier 0 is an error",     build_git,        [],                                    1, unfilled_tier0_fails),
    ("undo names what it misses",       build_with_gitignore, FILLED,                            0, undo_is_honest),
    ("no .gitignore -> no caveat [+]",  build_git,        FILLED,                                0, undo_omits_the_gitignore_caveat),
    # the undo itself, run rather than read
    ("undo restores exactly     [+]",   build_undo_target, FILLED,                               0, undo_is_exact),
    ("undo keeps edited files   [+]",   build_git,        FILLED,                                0, undo_keeps_edited_files),
    ("undo refuses with no record",     build_git,        ["--help"],                            0, undo_refuses_without_manifest),
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
