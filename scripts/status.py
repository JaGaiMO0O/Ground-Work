#!/usr/bin/env python3
"""status.py - regenerate the lower half of STATUS.md.

    python scripts/status.py
    python scripts/status.py --check      # is it up to date? exit 1 if not

STATUS.md has two zones separated by a marker line:

    everything ABOVE   written by a human: the goal ladder, the blockers
    everything BELOW   generated here from git, the handoffs and the validators

Deriving the lower half is the point. A file that is regenerated cannot go stale,
so the rot that kills every hand-maintained PROGRESS.md is removed rather than
policed. What is left above the line is intent, which changes rarely.

This never touches the human zone. If the marker is missing or duplicated it
refuses and changes nothing - a generator that eats somebody's hand-written text
gets deleted the first time it does so, and rightly.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import _lib as lib
from _lib import ROOT

STATUS = ROOT / "STATUS.md"
MARKER = lib.STATUS_MARKER


def _git(*args: str) -> str:
    result = lib.git(*args)
    return result.stdout.strip() if result.returncode == 0 else ""


def _clip(text: str, limit: int = 72) -> str:
    """Nothing pulled in from outside may be unbounded.

    A commit subject is *conventionally* short, but nothing enforces it - and a
    single long one is enough to push STATUS.md past its budget, which is how
    this was found. Everything derived from elsewhere gets clipped.
    """
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _branch_line() -> str:
    if not lib.is_git_repo():
        return "not a git repository"
    if not lib.has_commits():
        return "git repository with no commits yet"
    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or "?"
    sha = _git("rev-parse", "--short", "HEAD") or "?"
    subject = _clip(_git("log", "-1", "--pretty=%s"))
    when = _git("log", "-1", "--pretty=%cs")
    dirty = _git("status", "--porcelain")
    changed = len([l for l in dirty.splitlines() if l.strip()])
    suffix = f", {changed} uncommitted change(s)" if changed else ", clean"
    return f"{branch} @ {sha} ({when}){suffix}\n              \"{subject}\""


def _validation_line() -> str:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check.py"), "--quiet"],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    counts = re.search(r"(\d+) error\(s\), (\d+) warning\(s\)", result.stderr or "")
    if result.returncode == 0:
        return "clean"
    if counts:
        errors, warns = counts.group(1), counts.group(2)
        return f"{errors} error(s), {warns} warning(s)   -> python scripts/check.py"
    if result.returncode == 2:
        return "warnings only   -> python scripts/check.py"
    return "errors   -> python scripts/check.py"


def _handoff_line() -> str:
    folder = ROOT / "context" / "handoffs"
    if not folder.is_dir():
        return "none yet"
    files = sorted(
        (p for p in folder.glob("*.md") if re.match(r"^\d{4}-\d{2}-\d{2}-", p.name)),
        reverse=True,
    )
    if not files:
        return "none yet   -> python scripts/handoff.py \"<topic>\""
    newest = files[0]
    text = newest.read_text(encoding="utf-8", errors="replace")
    nxt = re.search(r"^Next:\s*(.+)$", text, re.M)
    line = newest.name
    if nxt and nxt.group(1).strip():
        line += f"\n              Next: {_clip(nxt.group(1))}"
    return line


def _areas_line(project) -> str:
    if project is None:
        return "project.yaml could not be read"
    total = len(project.areas)
    if not total:
        return "none declared yet   -> edit project.yaml"
    carded = sum(1 for a in project.areas if a.card.exists())
    wanted = [a.name for a in project.areas if a.survey and not a.card.exists()]
    line = f"{total} declared, {carded} with a card"
    if wanted:
        line += f"\n              awaiting a survey: {', '.join(wanted)}"
    return line


def _budget_line() -> str:
    """Advisory only. If telemetry is unreadable this goes quiet - it must never
    take the rest of the report down with it."""
    try:
        import _transcripts as tx

        tel = tx.read_for(ROOT)
        if not tel.ok:
            return "no session telemetry for this project"
        bits = []
        if tel.have_usage:
            cr = sum(s.cache_read for s in tel.sessions)
            cw = sum(s.cache_write for s in tel.sessions)
            if cr + cw:
                bits.append(f"cache {cr / (cr + cw) * 100:.0f}%")
            peak = max((s.peak_context for s in tel.sessions), default=0)
            if peak:
                bits.append(f"peak context {peak // 1000}k")
        if tel.have_tools:
            orient = sum(
                n for s in tel.sessions for k, n in s.tools.items()
                if k in tx.ORIENTATION_TOOLS
            )
            total = sum(sum(s.tools.values()) for s in tel.sessions)
            if total:
                bits.append(f"orientation {orient / total * 100:.0f}%")
        if not bits:
            return "telemetry present but unreadable - see scripts/_transcripts.py"
        return "; ".join(bits) + "   -> python scripts/usage.py"
    except Exception:
        return "unavailable"


def build_block(project) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows = [
        ("Generated", stamp),
        ("Branch", _branch_line()),
        ("Validation", _validation_line()),
        ("Last handoff", _handoff_line()),
        ("Areas", _areas_line(project)),
        ("Budget", _budget_line()),
    ]
    lines = ["", "## Where things stand", ""]
    lines += [f"{label + ':':<14}{value}" for label, value in rows]
    lines += [
        "",
        "<!-- Everything in this section is derived. Change the project, not this"
        " text. -->",
        "",
    ]
    return "\n".join(lines)


def split_zones(text: str):
    """-> (human_zone_including_marker, problem_or_None)"""
    count = text.count(MARKER)
    if count == 0:
        return None, (
            "the generated-zone marker is missing. Refusing to write, because "
            "without it there is no way to tell your text from generated text.\n"
            f"     Restore this line at the end of the human section:\n"
            f"     {MARKER} -->"
        )
    if count > 1:
        return None, (
            f"the marker appears {count} times. Refusing to write - leave exactly "
            "one."
        )
    head, _, _tail = text.partition(MARKER)
    end = text.index(MARKER) + len(MARKER)
    rest = text[end:]
    line_end = rest.find("\n")
    marker_line = MARKER + (rest[:line_end] if line_end != -1 else rest)
    return head + marker_line, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the generated zone is out of date")
    args = parser.parse_args()

    if not STATUS.exists():
        return lib.die(
            "STATUS.md not found. It is where 'where are we' lives.\n"
            "     Copy it from the template, or run python scripts/init.py"
        )

    text = STATUS.read_text(encoding="utf-8")
    human, problem = split_zones(text)
    if problem:
        return lib.die(f"STATUS.md: {problem}")

    project = None
    try:
        if lib.PROJECT_FILE.exists():
            project = lib.load_project()
    except SystemExit:
        project = None

    updated = human + "\n" + build_block(project)

    if args.check:
        # The timestamp always differs, so compare everything except it.
        strip = lambda s: re.sub(r"^Generated:.*$", "", s, flags=re.M).strip()
        if strip(updated) == strip(text):
            lib.ok("STATUS.md is up to date")
            return 0
        lib.warn("STATUS.md is out of date", )
        lib.info("       python scripts/status.py")
        return 1

    STATUS.write_text(updated, encoding="utf-8")

    # One settling pass. check.py validates STATUS.md, and we just rewrote it -
    # so the validation line we captured describes the file as it was a moment
    # ago. Rebuild once against the file that now exists; if that changes the
    # answer, the second write is the honest one. A status line reporting an
    # error that has already been fixed is worse than no status line.
    settled = human + "\n" + build_block(project)
    strip = lambda s: re.sub(r"^Generated:.*$", "", s, flags=re.M)
    if strip(settled) != strip(updated):
        STATUS.write_text(settled, encoding="utf-8")

    lib.ok("STATUS.md regenerated (human zone untouched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
