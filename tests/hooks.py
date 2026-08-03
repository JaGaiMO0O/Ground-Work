"""Exercise every guard decision. Blocks must block; nothing else may.

    python tests/hooks.py

The guard is the safety net for people who do not yet know what is expensive, so
its failure mode matters more than most. Two properties are tested:

  * the blocking rules actually block (exit 2)
  * everything else stays out of the way - a guard that cries wolf gets deleted,
    and then it protects nobody

Payloads are built with json.dumps rather than string formatting. Hand-writing
them puts unescaped Windows backslashes into JSON, the parse fails, and the guard
silently goes inert - which looks exactly like "no problems found".
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GUARD = REPO / "scripts" / "hooks" / "guard.py"
TMP = Path(tempfile.gettempdir()) / "guard-tests"

BLOCK, WARN, SILENT = "block", "warn", "silent"


def fire(payload: dict) -> str:
    proc = subprocess.run(
        [sys.executable, str(GUARD)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    if proc.returncode == 2:
        return BLOCK
    if proc.stdout.strip():
        return WARN
    return SILENT


def pre(tool: str, path: Path, **extra) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "cwd": str(REPO),
        "tool_input": {"file_path": str(path), **extra},
    }


def build_fixtures():
    TMP.mkdir(parents=True, exist_ok=True)
    big = TMP / "big.py"
    if not big.exists():
        big.write_text("x = 1\n" * 30000, encoding="utf-8")
    return big


def transcripts():
    """-> (long_session, short_session) or (None, None)."""
    root = Path(os.path.expanduser("~")) / ".claude" / "projects"
    if not root.is_dir():
        return None, None
    files = [p for p in root.rglob("*.jsonl") if p.stat().st_size > 500]
    if not files:
        return None, None
    files.sort(key=lambda p: p.stat().st_size)
    return files[-1], files[0]


def main() -> int:
    big = build_fixtures()
    long_session, short_session = transcripts()

    cases = [
        # --- must block -----------------------------------------------------
        ("read .env",                    pre("Read", REPO / ".env"), BLOCK),
        ("read a .pem",                  pre("Read", REPO / "x.pem"), BLOCK),
        ("read .netrc",                  pre("Read", REPO / ".netrc"), BLOCK),
        ("write into systems/",          pre("Write", REPO / "systems/x/A.java"), BLOCK),
        ("hand-edit .rgignore",          pre("Edit", REPO / ".rgignore"), BLOCK),
        ("hand-edit a schema snapshot",  pre("Edit", REPO / "map/api/schema.sql"), BLOCK),
        ("hand-edit an erd",             pre("Edit", REPO / "map/api/erd.mmd"), BLOCK),
        ("write into map/*/derived/",    pre("Write", REPO / "map/api/derived/F.xml"), BLOCK),
        ("edit STATUS generated zone",   pre("Edit", REPO / "STATUS.md",
                                            new_string="## Where things stand"), BLOCK),
        # --- must warn, but allow -------------------------------------------
        ("read a 176KB file",            pre("Read", big), WARN),
        ("pre-compact",                  {"hook_event_name": "PreCompact",
                                          "cwd": str(REPO)}, WARN),
        # --- must stay out of the way ---------------------------------------
        ("read a small file",            pre("Read", REPO / "CLAUDE.md"), SILENT),
        ("edit STATUS human zone",       pre("Edit", REPO / "STATUS.md",
                                            new_string="| **Now** | ship it |"), SILENT),
        ("edit ordinary source",         pre("Edit", REPO / "scripts/check.py"), SILENT),
        ("write a new doc",              pre("Write", REPO / "docs/notes.md"), SILENT),
        ("unrecognised event",           {"hook_event_name": "Whatever",
                                          "cwd": str(REPO)}, SILENT),
        ("empty payload",                {}, SILENT),
        ("malformed tool_input",         {"hook_event_name": "PreToolUse",
                                          "tool_name": "Read", "cwd": str(REPO),
                                          "tool_input": "not-a-dict"}, SILENT),
    ]

    if long_session:
        cases.append((
            "long session -> nudge",
            {"hook_event_name": "UserPromptSubmit", "cwd": str(REPO),
             "transcript_path": str(long_session)},
            WARN,
        ))
    if short_session:
        cases.append((
            "short session -> silence",
            {"hook_event_name": "UserPromptSubmit", "cwd": str(REPO),
             "transcript_path": str(short_session)},
            SILENT,
        ))
    cases.append((
        "unreadable transcript -> silence",
        {"hook_event_name": "UserPromptSubmit", "cwd": str(REPO),
         "transcript_path": str(TMP / "does-not-exist.jsonl")},
        SILENT,
    ))

    failures = 0
    print(f"{'case':34} {'got':>7} {'want':>7}  result")
    print("-" * 66)
    for name, payload, want in cases:
        got = fire(payload)
        good = got == want
        failures += 0 if good else 1
        print(f"{name:34} {got:>7} {want:>7}  {'ok' if good else 'FAILED'}")

    print("-" * 66)
    print(f"{len(cases) - failures}/{len(cases)} passed")
    if not long_session:
        print("note: no local transcripts, so the context-nudge cases were skipped")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
