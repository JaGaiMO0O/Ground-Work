#!/usr/bin/env python3
"""usage.py - where your context budget actually went.

Reads the session transcripts Claude Code keeps on this machine and turns them
into findings you can act on. It answers, from real data rather than advice:

    * which files you keep re-reading session after session
    * how much of your spend goes on orientation rather than work
    * how much context every session carries before you do anything
    * which sessions grew so long that every turn re-read a novel

    python scripts/usage.py              # this project
    python scripts/usage.py --all        # every project on this machine
    python scripts/usage.py --top 20

No token totals are converted to money. On a subscription the currency is your
usage window, not dollars, so everything here is reported in tokens and shares.

This tool is ADVISORY. If the transcript format changes it says so and stops -
it never guesses, and nothing else in the repo depends on it.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

import _lib as lib
import _transcripts as tx


def _fmt(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def _bar(fraction: float, width: int = 24) -> str:
    filled = max(0, min(width, round(fraction * width)))
    return "#" * filled + "." * (width - filled)


# Only text costs roughly len/4 tokens. A PDF is extracted, an image is tiled -
# guessing from byte count would put a fabricated number at the top of the
# report, which is worse than admitting we do not know.
TEXTUAL_SUFFIXES = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue", ".svelte",
    ".java", ".kt", ".scala", ".go", ".rs", ".rb", ".php", ".cs", ".vb", ".fs",
    ".c", ".h", ".cc", ".cpp", ".hpp", ".m", ".swift", ".pl", ".lua", ".r",
    ".jl", ".clj", ".ex", ".exs", ".erl", ".hs", ".dart", ".groovy",
    ".sql", ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
    ".yaml", ".yml", ".json", ".jsonl", ".toml", ".ini", ".cfg", ".conf",
    ".properties", ".xml", ".html", ".htm", ".css", ".scss", ".less",
    ".md", ".rst", ".txt", ".csv", ".tsv", ".ipynb",
    ".tf", ".proto", ".graphql", ".gradle", ".mk", ".cmake", ".dockerfile",
}
TEXTUAL_NAMES = {
    "makefile", "dockerfile", "rakefile", "gemfile", "procfile", "justfile",
    "cmakelists.txt", ".gitignore", ".env.example", ".rgignore",
}


def _file_tokens(path: Path) -> "int | None":
    """What re-reading this file costs, in tokens. None when we cannot tell."""
    if (
        path.suffix.lower() not in TEXTUAL_SUFFIXES
        and path.name.lower() not in TEXTUAL_NAMES
    ):
        return None
    try:
        if not path.is_file() or path.stat().st_size > 2_000_000:
            return None
        with path.open("rb") as handle:
            if b"\0" in handle.read(8192):
                return None
        return lib.estimate_tokens(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------


def section_overview(tel: tx.Telemetry) -> None:
    print(f"\n  {len(tel.sessions)} session(s) across "
          f"{len({s.project for s in tel.sessions})} project(s)"
          f"   [{tel.scanned_files} transcript file(s) read]")
    if tel.bad_lines:
        print(f"  {tel.bad_lines} unreadable line(s) skipped")

    if not tel.have_usage:
        print("\n  token accounting UNAVAILABLE - no usage records could be read.")
        print("  The transcript format may have changed. Reporting nothing rather")
        print("  than reporting zero, which would look like good news.")
        return

    out = sum(s.output for s in tel.sessions)
    cr = sum(s.cache_read for s in tel.sessions)
    cw = sum(s.cache_write for s in tel.sessions)
    print(f"\n  output written    {_fmt(out):>8}")
    print(f"  context re-read   {_fmt(cr):>8}   (cache hit, cheap)")
    print(f"  context written   {_fmt(cw):>8}   (cache miss, ~12x a hit)")


def section_cache(tel: tx.Telemetry) -> "list[str]":
    if not tel.have_usage:
        return []
    cr = sum(s.cache_read for s in tel.sessions)
    cw = sum(s.cache_write for s in tel.sessions)
    if cr + cw == 0:
        return []
    ratio = cr / (cr + cw)
    print(f"\n  CACHE EFFICIENCY   {_bar(ratio)}  {ratio * 100:.1f}%")
    if ratio >= 0.9:
        print("  Healthy. Your context is stable between turns, which is what you")
        print("  want - leave this alone.")
        return []
    print("  Low. Something near the top of your context changes every turn, so")
    print("  the whole prompt gets re-written instead of re-read.")
    return [
        "Cache hit ratio is low. Check that nothing volatile (a status file, a "
        "timestamp, a generated list) is being loaded into AGENTS.md or CLAUDE.md."
    ]


def section_orientation(tel: tx.Telemetry) -> "list[str]":
    if not tel.have_tools:
        print("\n  TOOL ANALYSIS UNAVAILABLE - no tool calls could be read.")
        return []
    counts: Counter = Counter()
    for session in tel.sessions:
        counts.update(session.tools)
    orient = sum(n for k, n in counts.items() if k in tx.ORIENTATION_TOOLS)
    work = sum(n for k, n in counts.items() if k in tx.WORK_TOOLS)
    other = sum(counts.values()) - orient - work
    total = orient + work + other
    if not total:
        return []
    share = orient / total
    print(f"\n  ORIENTATION SHARE  {_bar(share)}  {share * 100:.0f}%"
          f"   ({orient} orienting / {work} working / {other} other)")
    print("  Orientation is what you spend working out where things are, rather")
    print("  than changing anything. Under ~20% means your map is doing its job.")
    if share > 0.35:
        return [
            f"{share * 100:.0f}% of tool calls are orientation. Write area cards "
            "for whatever you keep looking up - see the re-read list below."
        ]
    return []


def section_baseline(tel: tx.Telemetry) -> "list[str]":
    """Context carried before any work happens: prompt + tool definitions."""
    if not tel.have_usage:
        return []
    baselines = [s.baseline_context for s in tel.sessions if s.baseline_context]
    if not baselines:
        return []
    baselines.sort()
    median = baselines[len(baselines) // 2]
    print(f"\n  STARTING CONTEXT   median {_fmt(median)} per session"
          f"   (lowest {_fmt(baselines[0])}, highest {_fmt(baselines[-1])})")
    print("  This is what every session carries before you ask for anything:")
    print("  instructions plus every enabled tool definition. It is paid on every")
    print("  turn, so it is the cheapest thing on this page to cut.")
    if median > 30_000:
        return [
            f"Every session starts at ~{_fmt(median)} before doing any work. "
            "Turn off MCP servers you are not using this task - see "
            "interfaces/mcp/servers.yaml."
        ]
    return []


def section_growth(tel: tx.Telemetry, top: int) -> "list[str]":
    if not tel.have_usage:
        return []
    rows = []
    for session in tel.sessions:
        main = session.main_turns
        if len(main) < 8:
            continue
        start, peak = main[0].context, session.peak_context
        if start and peak / start >= 3:
            rows.append((peak, peak / start, len(main), session))
    if not rows:
        return []
    rows.sort(reverse=True, key=lambda r: r[0])
    print("\n  LONG SESSIONS      context grew far past where it started")
    print(f"  {'peak/turn':>10}  {'growth':>7}  {'turns':>6}  session")
    for peak, factor, turns, session in rows[:top]:
        print(f"  {_fmt(peak):>10}  {factor:>6.1f}x  {turns:>6}  "
              f"{session.project[:38]}")
    worst = rows[0]
    return [
        f"One session reached {_fmt(worst[0])} of context per turn. Past roughly "
        "100k, every extra turn re-reads a novel. Write a handoff and start a "
        "fresh session instead: python scripts/handoff.py \"<topic>\""
    ]


def section_rereads(tel: tx.Telemetry, top: int, project) -> "list[str]":
    """The finding that changes behaviour."""
    if not tel.have_tools:
        return []

    sessions_by_file: dict = defaultdict(set)
    for session in tel.sessions:
        for path in session.reads:
            sessions_by_file[path].add(session.id)

    rows = []
    for path, sessions in sessions_by_file.items():
        if len(sessions) < 3:
            continue
        cost = _file_tokens(tx.native_path(path))
        wasted = cost * (len(sessions) - 1) if cost else None
        rows.append((len(sessions), wasted or 0, path, cost))
    if not rows:
        print("\n  RE-READS           nothing read in 3+ separate sessions. Good.")
        return []

    rows.sort(reverse=True, key=lambda r: (r[1], r[0]))
    known = sum(r[1] for r in rows)
    print(f"\n  RE-READS           {len(rows)} file(s) read in 3+ separate sessions")
    print("  Each of these was learned from scratch, more than once. A card or a")
    print("  recipe would have been read instead.\n")
    print(f"  {'sessions':>8}  {'wasted':>7}  file")
    for count, wasted, path, cost in rows[:top]:
        label = Path(path).name
        area = None
        if project is not None:
            try:
                rel = tx.native_path(path).resolve().relative_to(lib.ROOT).as_posix()
                found = project.area_for(rel)
                area = found.name if found else None
            except (ValueError, OSError):
                area = None
        suffix = f"   [area: {area}]" if area else ""
        print(f"  {count:>8}  {_fmt(wasted) if wasted else '   ?':>7}  "
              f"{label[:44]}{suffix}")
    if len(rows) > top:
        print(f"  ... and {len(rows) - top} more (--top {len(rows)} to see all)")
    if any(r[3] is None for r in rows[:top]):
        print("\n  '?' means the cost is not estimable from the file - a PDF, an")
        print("  image, or a binary. Still re-read, still paid for, not guessed at.")

    costed = sum(1 for r in rows if r[3] is not None)
    advice = [
        f"{len(rows)} file(s) were re-read across 3+ separate sessions"
        + (
            f". The {costed} text file(s) among them account for about "
            f"{_fmt(known)} tokens that a card would have replaced"
            if known
            else ""
        )
        + ". Promote those areas' cards with a full survey (ADR 0004): python scripts/new_card.py <area>"
    ]
    return advice


# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--all", action="store_true",
                        help="every project on this machine, not just this one")
    parser.add_argument("--path", metavar="DIR",
                        help="report on another project's directory, not this one")
    parser.add_argument("--top", type=int, default=10,
                        help="rows per table (default 10)")
    args = parser.parse_args()

    if args.all:
        tel = tx.read_all()
    elif args.path:
        # Baselining a project BEFORE adopting the scaffold into it: the tool
        # has to be able to look somewhere other than where it lives.
        tel = tx.read_for(Path(args.path).resolve())
    else:
        tel = tx.read_for(lib.ROOT)

    if not tel.ok:
        lib.warn("no readable session telemetry")
        for problem in tel.problems:
            lib.info(f"       {problem}")
        lib.info(
            "\n       This is advisory tooling only - nothing else depends on it.\n"
            "       If you have used Claude Code in this project before, the\n"
            "       transcript format may have changed; see scripts/_transcripts.py."
        )
        return 0

    project = None
    try:
        if lib.PROJECT_FILE.exists():
            project = lib.load_project()
    except SystemExit:
        project = None

    print("=" * 74)
    print("  WHERE YOUR CONTEXT BUDGET WENT")
    print("=" * 74)

    section_overview(tel)
    advice: list = []
    advice += section_cache(tel)
    advice += section_baseline(tel)
    advice += section_orientation(tel)
    advice += section_growth(tel, args.top)
    advice += section_rereads(tel, args.top, project)

    print("\n" + "=" * 74)
    if advice:
        print("  WHAT TO DO ABOUT IT")
        print("=" * 74)
        for i, item in enumerate(advice, 1):
            print(f"\n  {i}. {item}")
    else:
        print("  Nothing to flag. This project is being run efficiently.")
    print()

    for problem in tel.problems:
        lib.warn(problem)
    return 0


if __name__ == "__main__":
    sys.exit(main())
