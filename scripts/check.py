#!/usr/bin/env python3
"""check.py - validate this project's invariants.

A scaffold of templates with nothing validating them decays into a folder of
stale blanks. This is what stops that. Run it before you finish anything, and
in CI.

    exit 0   clean
    exit 1   at least one error
    exit 2   warnings only

Core rules apply to every project. A profile can add its own by exposing
`register(ctx)` and/or `EXTRA_CARD_SECTIONS` in profiles/<name>/rules.py.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import _lib as lib
from _lib import ROOT


@dataclass
class Finding:
    level: str  # "error" | "warn"
    group: str
    message: str
    fix: str = ""


FINDINGS: "list[Finding]" = []
NOTES: "list[str]" = []

# Placeholders that mean "this file was never filled in". Deliberately a fixed
# list rather than a <.*> regex, so real angle-bracket content is not flagged.
PLACEHOLDERS = (
    "<PROJECT_NAME>",
    "<ONE SENTENCE",
    "<DB_ROLE>",
    "<org/repo>",
    "<area>",
    "<system>",
    "<name>",
    "<date>",
    "<task name>",
    "<topic>",
    "<who>",
)

# The subset init.py fills in, and the only ones that mean "nobody personalized
# this". AGENTS.md legitimately contains <area> and <topic> in its command
# table - those are usage syntax, and flagging them would make the rule useless.
TIER0_PLACEHOLDERS = ("<PROJECT_NAME>", "<ONE SENTENCE", "<DB_ROLE>")


def error(group: str, message: str, fix: str = "") -> None:
    FINDINGS.append(Finding("error", group, message, fix))


def warn(group: str, message: str, fix: str = "") -> None:
    FINDINGS.append(Finding("warn", group, message, fix))


def note(message: str) -> None:
    NOTES.append(message)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


@dataclass
class Ctx:
    """Everything a rule needs. Passed to core rules and to profile rules
    alike, so a profile is not a second-class citizen."""

    project: lib.Project
    root: Path = ROOT
    error: Callable = error
    warn: Callable = warn
    note: Callable = note
    read: Callable = read
    rel: Callable = rel
    extra_card_sections: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tier 0 - the always-loaded budget
# ---------------------------------------------------------------------------


def check_tier0(ctx: Ctx) -> None:
    g = "tier 0"
    agents = ROOT / "AGENTS.md"
    claude = ROOT / "CLAUDE.md"

    if not agents.exists():
        error(g, "AGENTS.md is missing", "It is the router. Nothing works without it.")
        return

    text = read(agents)

    # An unfilled router is the one Tier 0 defect that costs on every turn of
    # every conversation and reads as fine. Measuring its token budget and
    # calling it well within it - which is all this rule used to do - is
    # measuring the wrong thing about a file whose first four lines are blanks.
    left = [p for p in TIER0_PLACEHOLDERS if p in text]
    if left and ctx.project.template:
        note("AGENTS.md is still template text, as it should be here "
             "(project.yaml declares 'template: true')")
    elif left:
        error(
            g,
            "AGENTS.md still contains template placeholders: " + ", ".join(left),
            "This is the first file every session reads, and it currently "
            "describes no project. python scripts/init.py, or fill them in.",
        )

    lines = text.splitlines()
    if len(lines) > lib.AGENTS_MD_MAX_LINES:
        error(
            g,
            f"AGENTS.md is {len(lines)} lines (max {lib.AGENTS_MD_MAX_LINES})",
            "Move detail into context/recipes/ or docs/. Tier 0 is a router, "
            "not a manual.",
        )

    total = lib.estimate_tokens(text) + lib.estimate_tokens(read(claude))
    budget = lib.TIER0_TOKEN_BUDGET
    if total > budget:
        error(
            g,
            f"Tier 0 is ~{total} tokens, over the {budget} budget",
            "This is paid on every single turn of every conversation.",
        )
    elif total > budget * 0.8:
        warn(g, f"Tier 0 is ~{total} tokens, close to the {budget} budget")
    else:
        note(f"Tier 0 ~{total} tokens of {budget} budget")

    if "## Where things are" not in text:
        warn(g, "AGENTS.md has no 'Where things are' routing table")

    if not claude.exists():
        warn(g, "CLAUDE.md is missing", "It should be a one-line pointer to AGENTS.md.")
    elif lib.estimate_tokens(read(claude)) > 150:
        warn(
            g,
            "CLAUDE.md is more than a pointer",
            "Two routers drift apart. Keep the content in AGENTS.md.",
        )


# ---------------------------------------------------------------------------
# project.yaml
# ---------------------------------------------------------------------------


def check_project(ctx: Ctx) -> None:
    g = "project"
    project = ctx.project

    for problem in project.errors:
        error(g, problem)

    if project.parser == "minyaml":
        note("PyYAML not installed - used the bundled subset parser")

    note(f"profile: {project.profile}")
    if project.template:
        note("template: true - this is the scaffold itself, not a project made "
             "from it")

    if not project.areas:
        note("no areas declared yet (expected for a fresh template)")
        return

    for area in project.areas:
        if area.kind == "repo" and area.ref and not lib.is_pinned(area.ref):
            warn(
                g,
                f"{area.name}: ref {area.ref!r} is a moving branch",
                "Pin to a tag or SHA, or the card will describe code that no "
                "longer exists.",
            )
        if area.kind == "local":
            for pattern in area.paths:
                stem = str(pattern).split("*", 1)[0].rstrip("/")
                if stem and not (ROOT / stem).exists():
                    warn(
                        g,
                        f"{area.name}: declared path {pattern!r} does not exist",
                        "An area pointing at nothing cannot be surveyed, and the "
                        "write guard cannot use it.",
                    )
        if area.survey and area.kind == "repo" and not area.sparse:
            warn(
                g,
                f"{area.name}: no 'sparse' paths declared",
                "The whole repo lands on disk and the agent may wander into it.",
            )


# ---------------------------------------------------------------------------
# map/ - the area cards
# ---------------------------------------------------------------------------


def card_gaps(text: str, extra_sections: "list[str]"):
    required = lib.REQUIRED_CARD_SECTIONS + list(extra_sections)
    missing_sections = [
        s for s in required
        if not re.search(rf"^##\s+{re.escape(s)}", text, re.M | re.I)
    ]
    missing_fields = [f for f in lib.REQUIRED_CARD_FIELDS if f not in text]
    if not any(f in text for f in lib.CARD_SOURCE_FIELDS):
        missing_fields.append(" or ".join(lib.CARD_SOURCE_FIELDS))
    return missing_sections, missing_fields


def check_cards(ctx: Ctx) -> None:
    g = "map"
    extra = ctx.extra_card_sections
    map_dir = lib.MAP_DIR

    template = map_dir / "_TEMPLATE" / "CARD.md"
    if not template.exists():
        warn(g, "map/_TEMPLATE/CARD.md is missing")
    else:
        sections, fields = card_gaps(read(template), extra)
        if sections or fields:
            error(
                g,
                "the card TEMPLATE itself is incomplete: missing "
                + ", ".join(sections + fields),
                "Every card generated from it will inherit the gap.",
            )

    # Worked examples are teaching material. If they rot they teach the wrong
    # shape, so they are held to the same standard as a real card.
    for card in sorted(ROOT.glob("examples/*/CARD.md")) + sorted(
        ROOT.glob("profiles/*/examples/*/CARD.md")
    ):
        sections, fields = card_gaps(read(card), extra)
        if sections or fields:
            error(
                g,
                f"{rel(card)}: example card is missing " + ", ".join(sections + fields),
            )

    declared = {a.name for a in ctx.project.areas}
    on_disk = (
        {d.name for d in map_dir.iterdir() if d.is_dir() and not d.name.startswith("_")}
        if map_dir.exists()
        else set()
    )

    for area in ctx.project.areas:
        if area.survey and not area.card.exists():
            error(
                g,
                f"{area.name}: survey: true but no card",
                f"python scripts/new_card.py {area.name}",
            )

    for orphan in sorted(on_disk - declared):
        warn(
            g,
            f"map/{orphan}/ has no matching area in project.yaml",
            "Either declare the area or delete the card. A card nobody can "
            "trace to an area is worse than none.",
        )

    for name in sorted(on_disk & declared):
        area = ctx.project.require(name)
        text = read(area.card)
        if not text:
            continue

        sections, fields = card_gaps(text, extra)
        if sections:
            error(g, f"{name}: card missing section(s) " + ", ".join(sections))
        if fields:
            error(g, f"{name}: card missing header field(s) " + ", ".join(fields))

        cost = lib.estimate_tokens(text)
        if cost > lib.CARD_TOKEN_BUDGET:
            error(
                g,
                f"{name}: card is ~{cost} tokens, over the "
                f"{lib.CARD_TOKEN_BUDGET} budget",
                "A card that costs this much is no longer cheaper than reading "
                "the code, which was the entire point. Split it or cut it.",
            )

        left = [p for p in PLACEHOLDERS if p in text]
        if left:
            warn(g, f"{name}: card still contains template placeholders "
                    + ", ".join(left))

        # Drift: the card describes a specific commit. If the pin has moved, the
        # card describes code that is no longer what sync.py fetches.
        match = re.search(r"Repo:\s*\S+\s*@\s*(\S+)", text)
        if match and area.ref and match.group(1) != area.ref:
            warn(
                g,
                f"{name}: card surveyed at {match.group(1)!r} but project.yaml "
                f"now pins {area.ref!r}",
                "Re-survey, or lower the confidence marker.",
            )

        conf = re.search(r"^Confidence:\s*(.+)$", text, re.M)
        if conf and "LOW" in conf.group(1).upper():
            uses = sum(
                1 for r in (ROOT / "context" / "recipes").glob("*.md")
                if name in read(r)
            )
            suffix = f", referenced by {uses} recipe(s)" if uses else ""
            note(f"{name} has LOW-confidence areas ({conf.group(1).strip()}){suffix}")


# ---------------------------------------------------------------------------
# recipes and handoffs
# ---------------------------------------------------------------------------


def check_recipes(ctx: Ctx) -> None:
    g = "recipes"
    folder = ROOT / "context" / "recipes"
    if not folder.exists():
        warn(g, "context/recipes/ is missing")
        return

    recipes = [p for p in folder.glob("*.md") if not p.name.startswith("_")]
    if not recipes:
        note("no recipes written yet - write them for your 3-5 commonest tasks")

    for path in recipes:
        text = read(path)
        if "Do NOT load" not in text:
            error(
                g,
                f"{rel(path)}: no 'Do NOT load:' section",
                "Naming what to skip is half of what a recipe is for.",
            )
        if "Done when" not in text:
            error(g, f"{rel(path)}: no 'Done when:' section")
        if "MCP servers" not in text:
            warn(
                g,
                f"{rel(path)}: does not state which MCP servers to enable",
                "Tool definitions are billed every turn. Silence defaults to "
                "leaving them all on.",
            )


def check_handoffs(ctx: Ctx) -> None:
    g = "handoffs"
    folder = ROOT / "context" / "handoffs"
    if not folder.exists():
        return
    for path in folder.glob("*.md"):
        if path.name.startswith("_"):
            continue
        if not re.match(r"^\d{4}-\d{2}-\d{2}-", path.name):
            warn(
                g,
                f"{rel(path)}: not named YYYY-MM-DD-<topic>.md",
                "Handoffs double as a chronological project log; the date has "
                "to sort.",
            )


# ---------------------------------------------------------------------------
# STATUS.md and RUNBOOK.md
# ---------------------------------------------------------------------------


def newest_handoff_date() -> "str | None":
    folder = ROOT / "context" / "handoffs"
    if not folder.is_dir():
        return None
    dates = [
        m.group(1)
        for p in folder.glob("*.md")
        if (m := re.match(r"^(\d{4}-\d{2}-\d{2})-", p.name))
    ]
    return max(dates) if dates else None


def check_status(ctx: Ctx) -> None:
    g = "status"
    path = ROOT / "STATUS.md"
    if not path.exists():
        warn(
            g,
            "STATUS.md is missing",
            "It is the only place that answers 'where is this project'. "
            "Handoffs are history; this is state.",
        )
        return

    text = read(path)

    if lib.STATUS_MARKER not in text:
        error(
            g,
            "STATUS.md has no generated-zone marker",
            "scripts/status.py refuses to run without it, because it cannot tell "
            "your text from generated text.",
        )

    cost = lib.estimate_tokens(text)
    if cost > lib.STATUS_TOKEN_BUDGET:
        error(
            g,
            f"STATUS.md is ~{cost} tokens, over the "
            f"{lib.STATUS_TOKEN_BUDGET} budget",
            "It is becoming a second source of truth. Point at handoffs, ADRs "
            "and the plan instead of restating them.",
        )

    human = text.split(lib.STATUS_MARKER)[0]
    left = [p for p in PLACEHOLDERS if p in human]
    if left:
        warn(g, "STATUS.md goal ladder is still template text: " + ", ".join(left))

    # The pristine ladder init.py and --adopt render from. Only meaningful where
    # init.py can still run - adoption carries neither file, and an adopted
    # project must not be nagged about a template it was never given.
    #
    # This rule exists because the absence of it cost a real adoption: once this
    # repo filled its own STATUS.md in, adoption started handing that file to
    # other projects, and nothing anywhere noticed.
    template = ROOT / "STATUS.template.md"
    if (ROOT / "scripts" / "init.py").is_file():
        if not template.is_file():
            warn(
                g,
                "STATUS.template.md is missing",
                "init.py and --adopt render STATUS.md from it. Without it, the "
                "next project inherits this one's goal ladder.",
            )
        elif "<what this phase is for" not in read(template):
            warn(
                g,
                "STATUS.template.md has been filled in",
                "It is the pristine copy, not a status. Whatever is written "
                "there is handed to the next project as its own.",
            )

    if not re.search(r"^phase:\s*\S+", text, re.M):
        warn(g, "STATUS.md has no 'phase:' in its front matter")

    # The narrow staleness rule: has anyone confirmed the goals lately?
    reviewed = re.search(r"^reviewed:\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.M)
    newest = newest_handoff_date()
    if reviewed and newest and newest > reviewed.group(1):
        from datetime import date

        try:
            r = date.fromisoformat(reviewed.group(1))
            n = date.fromisoformat(newest)
            if (n - r).days > 21:
                warn(
                    g,
                    f"STATUS.md goals last reviewed {reviewed.group(1)}, "
                    f"{(n - r).days} days before the newest handoff",
                    "Re-read the goal ladder. Change it or don't, then bump "
                    "'reviewed:'. Stated goals that have stopped matching the "
                    "work are worse than none.",
                )
        except ValueError:
            warn(g, f"STATUS.md 'reviewed:' is not a valid date: {reviewed.group(1)}")


def check_runbook(ctx: Ctx) -> None:
    g = "runbook"
    path = ROOT / "RUNBOOK.md"
    commands = ctx.project.commands or {}

    if not path.exists():
        warn(
            g,
            "RUNBOOK.md is missing",
            "Without it, an agent guesses how to build and test - or asks, which "
            "costs a round trip.",
        )
        return

    text = read(path)
    for name, command in commands.items():
        if not command:
            continue
        if str(command) not in text:
            warn(
                g,
                f"RUNBOOK.md does not mention the '{name}' command "
                f"declared in project.yaml",
                "The two must agree, or the runbook is fiction.",
            )

    if not commands:
        note("no commands declared in project.yaml - reproducibility starts there")
        return

    # Reproducibility: does the tool a command needs actually exist here?
    for name, command in commands.items():
        if not command:
            continue
        executable = str(command).split()[0]
        if executable in ("python", "python3", sys.executable):
            continue
        if lib.which(executable) is None:
            # "try: pip install -r requirements.txt" is useless advice when the
            # command that needs pip IS that install command. Suggest the
            # install step only to the commands that come after it.
            hint = None if name == "install" else commands.get("install")
            note(
                f"'{name}' command needs {executable!r}, which is not on PATH"
                + (f" - try: {hint}" if hint else "")
            )


# ---------------------------------------------------------------------------
# safety
# ---------------------------------------------------------------------------


def check_safety(ctx: Ctx) -> None:
    g = "safety"

    if not (ROOT / ".env.example").exists():
        warn(g, ".env.example is missing", "It documents what an adapter needs.")

    if not (ROOT / ".secrets-baseline").exists():
        warn(
            g,
            ".secrets-baseline is missing - the secret scan has not run",
            "python scripts/scan.py",
        )

    gitignore = read(ROOT / ".gitignore")
    for required in ("systems/", ".env"):
        if required not in gitignore:
            error(g, f".gitignore does not ignore {required!r}")

    if not lib.is_git_repo():
        note("not a git repo - skipped tracked-file checks")
        return
    if not lib.has_commits():
        note("no commits yet - skipped tracked-file checks")
        return

    tracked = lib.tracked_files()

    if any(f == ".env" or f.endswith("/.env") for f in tracked):
        error(
            g,
            ".env is tracked by git",
            "git rm --cached .env, then rotate everything that was in it.",
        )
    if ".env.example" not in tracked:
        warn(g, ".env.example is not tracked")

    in_systems = [f for f in tracked if f.startswith("systems/")]
    if in_systems:
        error(
            g,
            f"{len(in_systems)} file(s) tracked under systems/ (e.g. {in_systems[0]})",
            "systems/ is a reproducible working checkout and must stay "
            "gitignored. External source is never committed here.",
        )


# ---------------------------------------------------------------------------
# generated artifacts and adapters
# ---------------------------------------------------------------------------


def check_rgignore(ctx: Ctx) -> None:
    g = "search surface"
    path = ROOT / ".rgignore"
    if not path.exists():
        warn(g, ".rgignore is missing", "python scripts/sync.py")
        return
    if read(path) != lib.rgignore_text(ctx.project):
        warn(
            g,
            ".rgignore is out of sync with project.yaml",
            "python scripts/sync.py  (it is generated - do not hand-edit)",
        )


def check_adapters(ctx: Ctx) -> None:
    g = "adapters"
    for area in ctx.project.areas:
        for family in lib.ADAPTER_FAMILIES:
            name, path = lib.resolve_adapter(area, family)
            if name and path is None:
                error(
                    g,
                    f"{area.name}: adapter {name!r} declared for '{family}' but "
                    "not found on disk",
                    "See docs/adapters.md, or copy the nearest reference adapter.",
                )


def check_generated_headers(ctx: Ctx) -> None:
    g = "generated files"
    for pattern in ("map/*/schema.sql", "map/*/*.mmd", ".rgignore"):
        for path in ROOT.glob(pattern):
            head = read(path)[:400]
            if head and lib.GENERATED_HEADER not in head:
                warn(
                    g,
                    f"{rel(path)}: no {lib.GENERATED_HEADER} header",
                    "Generated files must say so, or somebody will hand-edit one.",
                )


# ---------------------------------------------------------------------------
# profile rules
# ---------------------------------------------------------------------------


def run_profile_rules(ctx: Ctx) -> None:
    try:
        module = lib.load_profile_rules(ctx.project)
    except Exception as exc:  # a broken profile must not hide core findings
        error(
            "profile",
            f"profiles/{ctx.project.profile}/rules.py failed to load: {exc}",
            "Core rules still ran. Fix the profile module.",
        )
        return
    if module is None:
        return
    register = getattr(module, "register", None)
    if callable(register):
        try:
            register(ctx)
        except Exception as exc:
            error(
                "profile",
                f"profiles/{ctx.project.profile}/rules.py register() raised: {exc}",
            )


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def report(quiet: bool) -> int:
    errors = [f for f in FINDINGS if f.level == "error"]
    warns = [f for f in FINDINGS if f.level == "warn"]

    for group in dict.fromkeys(f.group for f in FINDINGS):
        lib.info(f"\n  {group}")
        for finding in [f for f in FINDINGS if f.group == group]:
            emit = lib.err if finding.level == "error" else lib.warn
            emit(finding.message)
            if finding.fix:
                lib.info(f"       -> {finding.fix}")

    if NOTES and not quiet:
        lib.info("\n  notes")
        for n in NOTES:
            lib.info(f"       {n}")

    lib.info("")
    if errors:
        lib.err(f"{len(errors)} error(s), {len(warns)} warning(s)")
        return 1
    if warns:
        lib.warn(f"0 errors, {len(warns)} warning(s)")
        return 2
    lib.ok("all invariants hold")
    return 0


CORE_RULES = (
    check_tier0,
    check_project,
    check_cards,
    check_recipes,
    check_handoffs,
    check_status,
    check_runbook,
    check_safety,
    check_rgignore,
    check_adapters,
    check_generated_headers,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quiet", action="store_true", help="suppress notes")
    args = parser.parse_args()

    project = lib.load_project()

    extra_sections: list = []
    try:
        module = lib.load_profile_rules(project)
        if module is not None:
            extra_sections = list(getattr(module, "EXTRA_CARD_SECTIONS", []))
    except Exception:
        pass  # run_profile_rules reports the load failure properly

    ctx = Ctx(project=project, extra_card_sections=extra_sections)

    for rule in CORE_RULES:
        rule(ctx)
    run_profile_rules(ctx)

    return report(args.quiet)


if __name__ == "__main__":
    sys.exit(main())
