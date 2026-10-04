"""Break each invariant deliberately; confirm check.py notices.

A validator nobody has seen fail is a validator nobody should trust.

    python tests/invariants.py
    python tests/invariants.py --only legacy      # run matching cases only

Each case gets a fresh copy of the repo in the system temp directory, applies one
mutation, runs check.py, and asserts on both the exit code and a substring of the
output. Two kinds of case matter equally:

  * negative - break a rule, expect it to fire
  * positive control [+] - do something that LOOKS like a violation but is not,
    and expect silence. Those stop a rule over-firing, and they are how profile
    isolation is proved.

Notes on the mechanics, both learned the hard way:
  * work dirs live OUTSIDE the repo. Inside, a lingering git process holds the
    directory and rmtree fails with WinError 32 mid-run.
  * `git init` runs only for the cases that need tracked files. It is the slowest
    step by far and most rules do not involve git at all.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = Path(tempfile.gettempdir()) / f"invariant-harness-{os.getpid()}"
PRISTINE = BASE / "_pristine"
WORK = BASE / "case"  # reassigned per case

BASE_YAML = """project: t
profile: {profile}

commands:
  test: python -c "print(1)"

defaults:
  access: read-only
  survey: false

areas:
  - name: demo
    kind: repo
    url: git@example.com:acme/demo.git
    ref: v1.2.3
    access: read-only
    survey: true
    adapters:
      db: postgres
    sparse:
      - src/**
"""

LOCAL_YAML = """project: t
profile: general

commands:

areas:
  - name: app
    kind: local
    survey: false
    paths:
{paths}
"""

CARD = """# Area Card: demo
Repo: git@example.com:acme/demo.git @ v1.2.3  |  Surveyed: 2026-07-27  |  Owner: me
Confidence: HIGH on api

Stack: java8
Health: fine

## Owns (authoritative)
- thing - `src/Thing.java:12`

## Interfaces

### In
| Caller | Mechanism | Entry point | Notes |
|---|---|---|---|
| a | b | `src/A.java:3` | d |

### Out
- none

## Landmines
- none

## Do not read unless specifically needed
- none
"""

# A kind: local area whose card is checked against real files. Complete, so
# the local cases test citations and nothing else.
LOCAL_CARD = """# Area Card: app
Path: src/app/  |  Surveyed: 2026-10-04  |  Owner: me
Confidence: HIGH on everything

Stack: python
Health: fine

## Owns (authoritative)
- {claim}

## Interfaces
- none

## Landmines
- none

## Do not read unless specifically needed
- {skip}
"""

LOCAL_MAIN = """import os

from legacy_tax import rate

print(rate, os.sep)
"""

# A partial card: a source field and one section, nothing else.
PARTIAL_CARD = """# Area Card: demo
Repo: git@example.com:acme/demo.git @ v1.2.3

## Landmines
- totals round half-up per line, not per invoice - `src/Invoice.java:88`
"""

SEAMS = """# Seams: demo

## S1 - the boundary

| | |
|---|---|
| Quality | CLEAN |
| Evidence | 7 days of capture |
"""


def run(cmd, cwd=None, **kw):
    return subprocess.run(
        cmd, cwd=str(cwd or WORK), capture_output=True, text=True, **kw
    )


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
            if sys.version_info >= (3, 12):
                shutil.rmtree(path, onexc=force)
            else:
                shutil.rmtree(path, onerror=force)
        except OSError:
            time.sleep(0.3)


def build_pristine():
    nuke(BASE)
    BASE.mkdir(parents=True, exist_ok=True)
    # The files git says are the template, not the whole disk: a live worktree
    # under .claude/worktrees/ tripled this copy and the suite's runtime.
    sys.path.insert(0, str(REPO / "scripts"))
    import _lib

    for rel in _lib.template_files(REPO):
        if any(part in ("__pycache__", ".git", "systems") for part in rel.parts):
            continue
        destination = PRISTINE / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, destination)


def seed_initialised():
    """Make the copy look like init.py has been run on it.

    Every case declares its own project.yaml, which carries no `template: true`
    - so each one is a real project, and a real project with an unfilled Tier 0
    or an unfilled goal ladder is a finding. Seeding both here keeps unrelated
    cases from inheriting a failure that has nothing to do with what they test.

    STATUS.md is rendered from STATUS.template.md rather than patched, because
    this repo's own STATUS.md has been filled in since it started describing
    itself. Patching it silently stopped doing anything, which took the
    'STATUS goals gone stale' case down with it - it had no unreviewed date left
    to go stale from.
    """
    template = WORK / "STATUS.template.md"
    status = WORK / "STATUS.md"
    if template.is_file():
        text = template.read_text(encoding="utf-8")
        # Today, not a fixed date. A hardcoded one silently rots: the
        # staleness rule compares it against the newest handoff, so every
        # clean-baseline case started failing the day the repo wrote a
        # handoff three weeks newer than the fixture. The rule was right.
        from datetime import date

        text = text.replace("reviewed: <date>",
                            f"reviewed: {date.today().isoformat()}")
        text = text.replace(
            "<what this phase is for, in one line>", "keep the harness honest"
        )
        text = text.replace("<what follows it>", "ship it")
        text = text.replace(
            "<the condition that ends this phase - be specific enough to "
            "disagree with>",
            "every rule has a test",
        )
        status.write_text(text, encoding="utf-8")

    agents = WORK / "AGENTS.md"
    if agents.is_file():
        text = agents.read_text(encoding="utf-8")
        text = text.replace("<PROJECT_NAME>", "t")
        text = re.sub(r"<ONE SENTENCE[^>]*for>", "keep the harness honest", text)
        text = re.sub(r"<ONE SENTENCE[^>]*finished>", "every rule has a test", text)
        text = text.replace("<DB_ROLE>", "analyst_ro")
        agents.write_text(text, encoding="utf-8")


def seed_runbook(command: str):
    """project.yaml and RUNBOOK.md must agree, so record the declared command."""
    path = WORK / "RUNBOOK.md"
    if path.is_file():
        path.write_text(
            path.read_text(encoding="utf-8") + f"\n\n## Test\n\n```bash\n{command}\n```\n",
            encoding="utf-8",
        )


def fresh(index: int, use_git: bool):
    global WORK
    WORK = BASE / f"case-{index:02d}"
    shutil.copytree(PRISTINE, WORK)
    seed_initialised()
    if use_git:
        run(["git", "init", "-q"])
        run(["git", "config", "user.email", "t@t"])
        run(["git", "config", "user.name", "t"])
        run(["git", "config", "gc.auto", "0"])  # no background gc holding handles
        run(["git", "add", "-A"])
        run(["git", "commit", "-qm", "base"])


def write(rel: str, text: str):
    path = WORK / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def patch(rel: str, old: str, new: str):
    path = WORK / rel
    path.write_text(
        path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8"
    )


def commit(paths):
    run(["git", "add", "-f", *paths])
    run(["git", "commit", "-qm", "x"])


def apply_scaffold(profile: str):
    """What init.py does: overlay profiles/<p>/scaffold/** onto the project."""
    scaffold = WORK / "profiles" / profile / "scaffold"
    if scaffold.is_dir():
        shutil.copytree(scaffold, WORK, dirs_exist_ok=True)


TEST_COMMAND = 'python -c "print(1)"'


def setup(profile: str = "general", card: bool = True, seams: bool = False):
    write("project.yaml", BASE_YAML.format(profile=profile))
    seed_runbook(TEST_COMMAND)
    if profile != "general":
        apply_scaffold(profile)
    if card:
        write("map/demo/CARD.md", CARD)
    if seams:
        write("map/demo/seams.md", SEAMS)
    # .rgignore is generated from project.yaml; keep it in step so the search
    # surface rule does not fire in every unrelated case.
    # --rgignore-only: the declared repo area points at example.com, and a real
    # sync would block on DNS/SSH for ~15s per case.
    run([sys.executable, "scripts/sync.py", "--rgignore-only"])


def with_seams_section():
    patch("map/demo/CARD.md", "## Landmines", "## Seams\nS1 clean\n\n## Landmines")


# --- mutations -------------------------------------------------------------


def m_clean():
    setup()


def m_card_section_missing():
    setup()
    patch("map/demo/CARD.md", "## Do not read unless specifically needed\n- none\n", "")


def m_card_field_missing():
    setup()
    patch("map/demo/CARD.md", "Confidence: HIGH on api\n", "")


def m_card_no_source_field():
    setup()
    patch("map/demo/CARD.md", "Repo: git@example.com:acme/demo.git @ v1.2.3  |  ", "")


def m_card_over_budget():
    setup()
    path = WORK / "map" / "demo" / "CARD.md"
    path.write_text(
        path.read_text(encoding="utf-8") + ("\nfiller prose. " * 2000), encoding="utf-8"
    )


def m_survey_no_card():
    setup(card=False)


def m_ref_missing():
    setup()
    patch("project.yaml", "    ref: v1.2.3\n", "")


def m_ref_moving():
    setup()
    patch("project.yaml", "ref: v1.2.3", "ref: main")


def m_card_drift():
    setup()
    patch("project.yaml", "ref: v1.2.3", "ref: v9.9.9")


def m_unknown_profile():
    setup()
    patch("project.yaml", "profile: general", "profile: does-not-exist")


def m_local_no_paths():
    write("project.yaml", LOCAL_YAML.format(paths="      - scripts/**"))
    patch("project.yaml", "    paths:\n      - scripts/**\n", "")


def m_local_path_absent():
    write("project.yaml", LOCAL_YAML.format(paths="      - no/such/dir/**"))
    # --rgignore-only: the declared repo area points at example.com, and a real
    # sync would block on DNS/SSH for ~15s per case.
    run([sys.executable, "scripts/sync.py", "--rgignore-only"])


def m_local_path_ok():  # positive control
    write("project.yaml", LOCAL_YAML.format(paths="      - scripts/**"))
    # --rgignore-only: the declared repo area points at example.com, and a real
    # sync would block on DNS/SSH for ~15s per case.
    run([sys.executable, "scripts/sync.py", "--rgignore-only"])


def m_env_committed():
    setup()
    write(".env", "ORACLE_PASSWORD=hunter2real\n")
    commit([".env"])


def m_systems_committed():
    setup()
    write("systems/demo/Thing.txt", "legacy\n")
    commit(["systems/demo/Thing.txt"])


def m_recipe_missing_donot():
    setup()
    patch("context/recipes/trace-field.md", "Do NOT load:", "Skip:")


def m_template_broken():
    setup()
    patch("map/_TEMPLATE/CARD.md", "## Landmines", "## Gotchas")


def m_orphan_card():
    setup()
    write("map/ghost/CARD.md", CARD)


def m_adapter_missing():
    setup()
    patch("project.yaml", "db: postgres", "db: sqlserver")


def m_tier0_bloated():
    setup()
    path = WORK / "AGENTS.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\nfiller line\n" * 200, encoding="utf-8"
    )


def m_tier0_unfilled():
    """An adopted project arrived with `# Project: <PROJECT_NAME>` and check.py
    reported its token budget and nothing else."""
    setup()
    patch("AGENTS.md", "# Project: t", "# Project: <PROJECT_NAME>")


def m_tier0_usage_syntax():  # positive control
    """AGENTS.md's command table legitimately contains <area> and <topic>. A
    rule that reads every angle bracket as an unfilled blank is a rule nobody
    can keep clean."""
    setup()
    patch("AGENTS.md", "| `python scripts/scan.py` | Secret scan |",
          "| `python scripts/scan.py` | Secret scan |\n"
          "| `python scripts/new_card.py <area>` | Start a card for <area> |")


def m_template_repo_exempt():  # positive control
    """The scaffold itself is meant to hold placeholders - that is what it is
    for. `template: true` is how it says so, and init.py deletes the line."""
    setup()
    patch("AGENTS.md", "# Project: t", "# Project: <PROJECT_NAME>")
    patch("project.yaml", "profile: general", "profile: general\ntemplate: true")


def setup_local(claim: str, skip: str = "none"):
    write("src/app/main.py", LOCAL_MAIN)
    write("src/app/legacy_tax.py", "rate = 0.2\n")
    write("project.yaml", LOCAL_YAML.format(paths="      - src/app/**"))
    write("map/app/CARD.md", LOCAL_CARD.format(claim=claim, skip=skip))
    # --rgignore-only: the declared repo area points at example.com, and a real
    # sync would block on DNS/SSH for ~15s per case.
    run([sys.executable, "scripts/sync.py", "--rgignore-only"])


def m_claim_uncited():
    setup()
    patch("map/demo/CARD.md", "## Landmines\n- none", "## Landmines\n- totals round half-up")


def m_claim_unverified():  # positive control
    setup()
    patch("map/demo/CARD.md", "## Landmines\n- none",
          "## Landmines\n- totals round half-up (unverified)")


def m_claim_per_person():  # positive control
    setup()
    patch("map/demo/CARD.md", "## Landmines\n- none",
          "## Landmines\n- totals round half-up (per Rania, 2026-10-04)")


def m_local_citation_missing():
    setup_local("the tax rate - `src/app/nope.py:2`")


def m_local_citation_past_end():
    setup_local("the tax rate - `src/app/main.py:2-40`")


def m_skip_no_reason():
    setup()
    patch("map/demo/CARD.md", "## Do not read unless specifically needed\n- none",
          "## Do not read unless specifically needed\n- `src/old/` - unused")


def m_skip_referenced():
    setup_local("the tax rate - `src/app/main.py:3`",
                "`src/app/legacy_tax.py` - no calls in 12 months of access logs")


def m_skip_ignores_worktrees():  # positive control
    """A Claude Code worktree is a full copy of the repo that git ignores. Its
    copy of a dead file, and anything in it naming one, is not the project."""
    # Assembled, not written out: this file is copied into the case, and the
    # whole name in it would be a real reference.
    dead = "old_" + "report"
    setup_local("the tax rate - `src/app/main.py:3`",
                f"`src/{dead}.py` - no calls in 12 months of access logs")
    write(f"src/{dead}.py", "def run():\n    pass\n")
    write(f".claude/worktrees/w1/src/{dead}.py", "def run():\n    pass\n")
    write(".claude/worktrees/w1/src/app/caller.py", f"import {dead}\n")


def m_claim_per_bad_date():
    setup()
    patch("map/demo/CARD.md", "## Landmines\n- none",
          "## Landmines\n- totals round half-up (per Rania, 2026-99-99)")


def m_partial_survey_false():  # positive control
    setup()
    patch("project.yaml", "survey: true", "survey: false")
    write("map/demo/CARD.md", PARTIAL_CARD)


def m_partial_survey_true():
    setup()
    write("map/demo/CARD.md", PARTIAL_CARD)


def m_card_at_2400():  # positive control
    """Over the old 2,000 budget, under the new 2,500. Prose, not claims."""
    setup()
    path = WORK / "map" / "demo" / "CARD.md"
    text = path.read_text(encoding="utf-8") + "\n"
    filler = "filler prose. " * ((2400 * 4 - len(text)) // 14)
    path.write_text(text + filler + "\n", encoding="utf-8")


def m_example_card_broken():
    setup()
    patch(
        "profiles/legacy-modernization/examples/billing-legacy/CARD.md",
        "## Owns",
        "## Stuff",
    )


def m_rgignore_stale():
    setup()
    (WORK / ".rgignore").write_text("# hand-edited\n", encoding="utf-8")


# --- STATUS.md and RUNBOOK.md ----------------------------------------------


def m_status_no_marker():
    setup()
    patch("STATUS.md", "<!-- BELOW THIS LINE IS GENERATED by scripts/status.py", "<!-- x")


def m_status_over_budget():
    setup()
    path = WORK / "STATUS.md"
    path.write_text(
        path.read_text(encoding="utf-8") + ("\nrestating the whole plan. " * 400),
        encoding="utf-8",
    )


def m_status_missing():
    setup()
    (WORK / "STATUS.md").unlink()


def m_status_template_gone():
    """Delete the pristine ladder and adoption silently starts shipping this
    project's own STATUS.md again - which is exactly how it happened."""
    setup()
    (WORK / "STATUS.template.md").unlink()


def m_status_goals_stale():
    setup()
    # Both dates stated here, relative to each other. This case used to lean on
    # seed_status()'s hardcoded review date already being old enough - so it
    # passed only for as long as that stayed true, and the positive controls
    # broke the day the repo wrote a handoff three weeks newer than it.
    from datetime import date, timedelta

    patch("STATUS.md", f"reviewed: {date.today().isoformat()}",
          f"reviewed: {(date.today() - timedelta(days=40)).isoformat()}")
    stamp = (date.today() - timedelta(days=1)).isoformat()
    write(f"context/handoffs/{stamp}-later-work.md",
          "# Handoff\n\nNext: something\n")


def m_runbook_missing_command():
    setup()
    patch("RUNBOOK.md", TEST_COMMAND, "# nothing here")


def m_runbook_missing():
    setup()
    (WORK / "RUNBOOK.md").unlink()


# --- profile isolation -----------------------------------------------------


def m_legacy_needs_seams():
    """Under the legacy profile a card without Seams is an error..."""
    setup(profile="legacy-modernization", card=True, seams=True)


def m_general_ignores_seams():  # positive control
    """...and under general it is not."""
    setup(profile="general", card=True, seams=False)


def m_legacy_complete():  # positive control
    setup(profile="legacy-modernization", card=True, seams=True)
    with_seams_section()


def m_legacy_seams_no_evidence():
    setup(profile="legacy-modernization", card=True, seams=True)
    with_seams_section()
    patch("map/demo/seams.md", "| Evidence | 7 days of capture |", "")


def m_legacy_foreign_source():
    setup(profile="legacy-modernization", card=True, seams=True)
    with_seams_section()
    write("docs/Leak.java", "class X {}\n")
    commit(["docs/Leak.java"])


def m_general_allows_own_source():  # positive control
    """A .java file in a project you own is just code, not a violation."""
    setup(profile="general")
    write("docs/Mine.java", "class X {}\n")
    commit(["docs/Mine.java"])


def m_legacy_derived_exempt():  # positive control
    setup(profile="legacy-modernization", card=True, seams=True)
    with_seams_section()
    write("map/demo/derived/Form.java", "class X {}\n")
    commit(["map/demo/derived/Form.java"])


#  name                               mutation                     exit  expect                          git
CASES = [
    ("clean baseline",                 m_clean,                     0, "",                              False),
    ("card section missing",           m_card_section_missing,      1, "missing section",               False),
    ("card field missing",             m_card_field_missing,        1, "header field",                  False),
    ("card has no source field",       m_card_no_source_field,      1, "Path: or Repo:",                False),
    ("card over token budget",         m_card_over_budget,          1, "over the",                      False),
    ("survey:true, no card",           m_survey_no_card,            1, "no card",                       False),
    ("ref absent entirely",            m_ref_missing,               1, "requires 'ref'",                False),
    ("ref is a moving branch",         m_ref_moving,                2, "moving branch",                 False),
    ("card ref drift",                 m_card_drift,                2, "now pins",                      False),
    ("unknown profile",                m_unknown_profile,           1, "no directory under profiles/",  False),
    ("local area with no paths",       m_local_no_paths,            1, "requires 'paths'",              False),
    ("local area path absent",         m_local_path_absent,         2, "does not exist",                False),
    ("local area path present    [+]", m_local_path_ok,             0, "",                              False),
    ("recipe lacks 'Do NOT load'",     m_recipe_missing_donot,      1, "Do NOT load",                   False),
    ("card TEMPLATE broken",           m_template_broken,           1, "TEMPLATE itself",               False),
    ("orphan card dir",                m_orphan_card,               2, "no matching area",              False),
    ("adapter declared, absent",       m_adapter_missing,           1, "not found on disk",             False),
    ("Tier 0 over line limit",         m_tier0_bloated,             1, "max 150",                       False),
    ("Tier 0 never filled in",         m_tier0_unfilled,            1, "template placeholders",         False),
    ("Tier 0 usage syntax       [+]",  m_tier0_usage_syntax,        0, "",                              False),
    ("template repo is exempt   [+]",  m_template_repo_exempt,      0, "",                              False),
    ("example card broken",            m_example_card_broken,       1, "example card is missing",       False),
    (".rgignore hand-edited",          m_rgignore_stale,            2, "out of sync",                   False),
    ("STATUS marker corrupted",        m_status_no_marker,          1, "no generated-zone marker",      False),
    ("STATUS over budget",             m_status_over_budget,        1, "over the",                      False),
    ("STATUS missing",                 m_status_missing,            2, "STATUS.md is missing",          False),
    ("STATUS goals gone stale",        m_status_goals_stale,        2, "last reviewed",                 False),
    ("STATUS.template.md deleted",     m_status_template_gone,      2, "STATUS.template.md is missing", False),
    ("RUNBOOK omits a command",        m_runbook_missing_command,   2, "does not mention the 'test'",   False),
    ("RUNBOOK missing",                m_runbook_missing,           2, "RUNBOOK.md is missing",         False),
    # card contracts C1-C3 (context/tasks/README.md)
    ("card claim uncited",             m_claim_uncited,             1, "claim has no citation",         False),
    ("claim marked unverified   [+]",  m_claim_unverified,          0, "",                              False),
    ("claim cited per person    [+]",  m_claim_per_person,          0, "",                              False),
    ("interview date invalid",         m_claim_per_bad_date,        1, "invalid date",                  False),
    ("local citation file missing",    m_local_citation_missing,    1, "does not exist",                False),
    ("local citation line past end",   m_local_citation_past_end,   1, "has only",                      False),
    ("skip entry without reason",      m_skip_no_reason,            1, "needs a reason",                False),
    ("skip entry referenced elsewhere", m_skip_referenced,          2, "referenced from",               False),
    ("partial card, survey false [+]", m_partial_survey_false,      0, "",                              False),
    ("partial card, survey true",      m_partial_survey_true,       1, "missing section",               False),
    ("card at 2,400 tokens      [+]",  m_card_at_2400,              0, "",                              False),
    # these need real tracked files
    ("skip check ignores worktree copies [+]", m_skip_ignores_worktrees, 0, "",                       True),
    (".env committed",                 m_env_committed,             1, ".env is tracked",               True),
    ("file tracked under systems/",    m_systems_committed,         1, "tracked under systems/",        True),
    # profile isolation
    ("legacy: complete card     [+]",  m_legacy_complete,           0, "",                              False),
    ("legacy: card needs Seams",       m_legacy_needs_seams,        1, "Seams",                         False),
    ("general: Seams not needed [+]",  m_general_ignores_seams,     0, "",                              False),
    ("legacy: seam has no Evidence",   m_legacy_seams_no_evidence,  2, "Evidence",                      False),
    ("legacy: foreign source",         m_legacy_foreign_source,     1, "legacy source file",            True),
    ("general: own source is ok [+]",  m_general_allows_own_source, 0, "",                              True),
    ("legacy: derived/ exempt   [+]",  m_legacy_derived_exempt,     0, "",                              True),
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

    build_pristine()
    failures = 0
    started = time.time()

    print(f"{'case':34} {'exit':>4} {'want':>4}  result", flush=True)
    print("-" * 74, flush=True)
    for index, (name, mutate, want_code, want_text, use_git) in enumerate(cases):
        fresh(index, use_git)
        mutate()
        proc = run([sys.executable, "scripts/check.py"])
        output = proc.stdout + proc.stderr
        code_ok = proc.returncode == want_code
        text_ok = (want_text in output) if want_text else True
        good = code_ok and text_ok
        failures += 0 if good else 1
        note = (
            "ok" if good
            else "WRONG EXIT" if not code_ok
            else f"missing text {want_text!r}"
        )
        print(f"{name:34} {proc.returncode:>4} {want_code:>4}  {note}", flush=True)
        if not good:
            print("   ---- output ----", flush=True)
            for line in output.strip().splitlines()[:16]:
                print("   " + line, flush=True)

    if args.keep:
        print(f"kept: {BASE}", flush=True)
    else:
        nuke(BASE)
    print("-" * 74, flush=True)
    print(
        f"{len(cases) - failures}/{len(cases)} passed in {time.time() - started:.0f}s"
        "   ([+] = positive control)",
        flush=True,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
