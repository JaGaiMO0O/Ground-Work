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
import os
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
STATUS = ROOT / "STATUS.md"
STATUS_TEMPLATE = ROOT / "STATUS.template.md"

PROJECT_TOKEN = "<PROJECT_NAME>"
PURPOSE_RE = re.compile(r"<ONE SENTENCE[^>]*for>")
DONE_RE = re.compile(r"<ONE SENTENCE[^>]*finished>")
DB_ROLE_TOKEN = "<DB_ROLE>"

# The one line project.yaml carries to say "this is the scaffold, not a project
# made from it". check.py reads it to decide whether unfilled Tier 0
# placeholders are expected or an error. Removed the moment init runs.
TEMPLATE_MARKER_RE = re.compile(
    r"\n?^# TEMPLATE MARKER[^\n]*\n(?:^#[^\n]*\n)*^template:[ \t]*true[ \t]*$\n?",
    re.M,
)

STATUS_PURPOSE_TOKEN = "<what this phase is for, in one line>"
STATUS_DONE_TOKEN = (
    "<the condition that ends this phase - be specific enough to disagree with>"
)


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


def personalized_agents(text: str, project: str, purpose: str, done: str,
                        db_role: str) -> str:
    """Fill in the Tier 0 router. Used by both plain init and --adopt.

    A lambda rather than a plain replacement string, because re.sub reads
    backslashes in the replacement - a purpose containing a Windows path used to
    raise, or silently eat characters.
    """
    text = text.replace(PROJECT_TOKEN, project)
    text = text.replace(DB_ROLE_TOKEN, db_role or "none")
    if purpose:
        text = PURPOSE_RE.sub(lambda _m: purpose, text)
    if done:
        text = DONE_RE.sub(lambda _m: done, text)
    return text


def unfilled(text: str) -> "list[str]":
    """Which of the tokens init substitutes are still in there. `<area>` and
    `<topic>` in the command table are usage syntax, not blanks - so this asks
    only about the three that mean nobody personalized the file."""
    return [t for t in (PROJECT_TOKEN, "<ONE SENTENCE", DB_ROLE_TOKEN) if t in text]


def render_status(purpose: str = "", done: str = "") -> "str | None":
    """The pristine goal ladder, dated, with whatever we were told filled in.

    Always from STATUS.template.md, never from STATUS.md. Once this repo started
    describing itself, copying STATUS.md into another project handed it Ground
    Work's goal ladder and blockers - stated confidently, in the file AGENTS.md
    routes to for 'where this project stands'.
    """
    if not STATUS_TEMPLATE.is_file():
        return None
    from datetime import date

    text = STATUS_TEMPLATE.read_text(encoding="utf-8")
    text = text.replace("reviewed: <date>", f"reviewed: {date.today().isoformat()}")
    if purpose:
        text = text.replace(STATUS_PURPOSE_TOKEN, purpose)
    if done:
        text = text.replace(STATUS_DONE_TOKEN, done)
    return text


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


def merge_gitignore(target: Path, dry_run: bool) -> "tuple[str, str]":
    """Append what we need, never rewrite what is there.

    -> (outcome, message), outcome one of modified | created | unchanged.

    The outcome is not just for reporting. It decides what the undo message may
    honestly promise: `git clean` deletes a .gitignore adoption created, and
    cannot touch one adoption modified, because that one is tracked.
    """
    path = target / ".gitignore"
    existed = path.is_file()
    existing = path.read_text(encoding="utf-8") if existed else ""
    missing = [
        line for line in ("systems/", ".env", "integration/fixtures/**/raw/")
        if line not in existing
    ]
    if not missing:
        return "unchanged", "already covers what we need"
    if not dry_run:
        path.write_text(existing.rstrip("\n") + "\n" + GITIGNORE_ADDITIONS,
                        encoding="utf-8")
    outcome = "modified" if existed else "created"
    return outcome, f"{outcome}, appended {len(missing)} entry(ies)"


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

    # AGENTS.md is Tier 0 - the router, loaded on every turn. Plain init has
    # always filled it in; adopt never did, so every adopted project opened with
    # `# Project: <PROJECT_NAME>`. Ask if there is somebody to ask. If not, the
    # placeholders stay and check.py fails on them at the end of this run: rule
    # 2 forbids inventing a purpose, but an unfilled router must be loud.
    purpose, done = args.purpose, args.done
    if not (purpose and done) and sys.stdin.isatty():
        lib.info(
            "\n  Two questions. The answers go into AGENTS.md, which is loaded on\n"
            "  every turn of every conversation - so keep them to one line.\n"
            "  Enter skips, and check.py will fail until they are filled in.\n"
        )
        purpose = purpose or ask("Purpose (one sentence)")
        done = done or ask("Done = (one sentence)")

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
    status_text = render_status(purpose or "", done or "")
    if status_text is None:
        lib.warn("STATUS.template.md not found - no STATUS.md written")
    else:
        generated.append((target / "STATUS.md", status_text))

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

    gitignore_outcome, gitignore_note = merge_gitignore(target, args.dry_run)
    lib.ok(f".gitignore: {gitignore_note}")

    # Everything we run inside the target runs without bytecode. A __pycache__
    # left under scripts/ survives `git clean -fd` in any project that ignores
    # *.pyc, which quietly makes the undo above untrue - found by running the
    # undo rather than by reading it. Not writing the file beats documenting it.
    quiet_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    if not args.dry_run:
        # Generate the search surface now, so the very first grep in the adopted
        # project already excludes noise and credential-bearing files.
        subprocess.run(
            [sys.executable, str(target / "scripts" / "sync.py"), "--rgignore-only"],
            cwd=str(target), capture_output=True, env=quiet_env,
        )
        lib.ok(".rgignore generated from the detected areas")
        # sync.py also creates this, and it is invisible to the undo below - so
        # report it. An adoption that writes a file it does not name is exactly
        # how the undo instructions came to be wrong.
        if (target / "systems" / ".sync-state.json").is_file():
            lib.ok("systems/.sync-state.json created (empty - nothing to check "
                   "out yet)")
    lib.ok(f"scaffold: {counts['add']} added, {counts['proposed']} proposed "
           f"alongside existing files, {counts['skip']} already present")

    if args.dry_run:
        lib.info("\n  dry run - nothing was written\n")
        return 0

    agents_left: "list[str]" = []
    agents_path = next(
        (_adopt.final_path(d, a) for _s, d, a in plan
         if d.name == "AGENTS.md" and a != "skip"),
        None,
    )
    if agents_path is not None and agents_path.is_file():
        text = personalized_agents(
            agents_path.read_text(encoding="utf-8"), name, purpose or "",
            done or "", args.db_role,
        )
        agents_path.write_text(text, encoding="utf-8")
        agents_left = unfilled(text)
        lib.ok(f"personalized {agents_path.name}")

    proposed = [d for _s, d, a in plan if a == "proposed"]
    if proposed:
        lib.info("\n  These already existed, so ours are alongside as .proposed:")
        for path in proposed[:8]:
            lib.info(f"       {path.relative_to(target).as_posix()}.proposed")
        lib.info("       Merge what you want and delete the rest. Nothing was "
                 "overwritten.")

    if tracked:
        # Written once as "-nd lists everything, -fd removes it" and wrong the
        # same day. git clean only ever touches UNTRACKED, UNIGNORED files, and
        # adoption produces one of each kind it misses. The honest version names
        # what it does not cover rather than reaching for -fdx, which would also
        # delete the venv, the .env and every other ignored file worth keeping.
        lines = [
            "\n  If you want out:",
            "       git clean -nd      lists the files adoption ADDED",
            "       git clean -fd      removes them",
            "  Exact only because the tree was clean before this ran. What that",
            "  does NOT cover:",
        ]
        if gitignore_outcome == "modified":
            lines += [
                "    - .gitignore was MODIFIED, not added, and git clean never",
                "      touches a tracked file:  git checkout -- .gitignore",
            ]
        lines += [
            "    - systems/ is ignored by the .gitignore block above, so plain",
            "      -fd skips it:  git clean -fdx systems/",
            "  Do not reach for a bare `git clean -fdx` to cover both. It would",
            "  also delete your venv, your .env, and everything else ignored.",
        ]
        lib.info("\n".join(lines))

    steps = [
        "AGENTS.md      - fill in the purpose and done lines; it is read every turn"
        if agents_left else
        "AGENTS.md      - check the purpose and done lines read right",
        "project.yaml   - fix the proposed areas; they are a guess",
        "RUNBOOK.md     - verify the detected commands actually run",
        "python scripts/scan.py",
        "python scripts/usage.py    - see what this project has cost so far",
    ]
    lib.info(
        "\n  Next, in " + target.name + ":\n"
        + "\n".join(f"    {i}. {s}" for i, s in enumerate(steps, 1))
        + "\n\n  Then pick the busiest area and write its card.\n"
    )

    if agents_left:
        lib.warn("AGENTS.md is still template text: " + ", ".join(agents_left))
        lib.info(
            "       Tier 0 is the first thing every session reads, and check.py\n"
            "       below will fail on it. Fill it in, or re-run with --purpose\n"
            "       and --done."
        )

    lib.info("  Validating the result...\n")
    code = subprocess.run(
        [sys.executable, str(target / "scripts" / "check.py")], cwd=str(target),
        env=quiet_env,
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
    edits.append((AGENTS, personalized_agents(
        AGENTS.read_text(encoding="utf-8"), project, purpose, done, db_role)))

    edits.append((README, README.read_text(encoding="utf-8")
                  .replace(PROJECT_TOKEN, project)))

    project_text = PROJECT.read_text(encoding="utf-8").replace(PROJECT_TOKEN, project)
    # Set the line rather than substituting the token, the way `profile:`
    # already is. Since this repo started describing itself the token is gone
    # from its own project.yaml, so replacement alone left a new project called
    # `ground-work`.
    project_text = re.sub(r"^project:.*$", f"project: {project}",
                          project_text, count=1, flags=re.M)
    project_text = re.sub(r"^profile:.*$", f"profile: {profile}",
                          project_text, count=1, flags=re.M)
    # This has stopped being the template the moment it becomes a project.
    project_text = TEMPLATE_MARKER_RE.sub("\n", project_text)
    edits.append((PROJECT, project_text))

    # The purpose and done answers ARE the goal ladder. Ask once, fill both.
    #
    # Rendered from STATUS.template.md rather than patched in place: this repo's
    # own STATUS.md is filled in, so patching it left the new project holding
    # Ground Work's goal ladder - the same defect --adopt had.
    status_text = render_status(purpose, done)
    if status_text is None:
        lib.warn("STATUS.template.md not found - STATUS.md left as it is")
    else:
        edits.append((STATUS, status_text))

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
