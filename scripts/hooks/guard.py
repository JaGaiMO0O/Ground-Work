#!/usr/bin/env python3
"""guard.py - the guardrails, wired to Claude Code hook events.

One script, several events. Reads the hook payload on stdin and decides.

    exit 0  allow. Anything on stdout is shown, and is how a warning is given.
    exit 2  BLOCK. stderr goes back to the model as the reason.

Design rules, in priority order:

  1. NEVER crash and never block by accident. Any unexpected condition exits 0.
     A guard that stops work because of its own bug gets deleted, and then it
     protects nobody.
  2. Warn by default; block only what is genuinely harmful - reading secrets,
     writing to a read-only checkout, hand-editing a generated file. Everything
     about cost is a warning, because being expensive is not being wrong.
  3. Every warning names the cheaper alternative. "That file is large" is
     nagging; "that file is large, grep it or read the area card" is help.
  4. Inert outside a project. No project.yaml, no opinions.

Thresholds can be overridden with GUARD_READ_BYTES and GUARD_CONTEXT_TOKENS.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# scripts/ is the parent of hooks/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

READ_BYTES = int(os.environ.get("GUARD_READ_BYTES", "100000"))
CONTEXT_TOKENS = int(os.environ.get("GUARD_CONTEXT_TOKENS", "120000"))

SECRET_NAMES = {".env", ".secrets-baseline.raw.json", "id_rsa", ".netrc",
                ".pgpass", "credentials.json", ".credentials.json"}
SECRET_SUFFIXES = {".pem", ".p12", ".jks", ".key", ".keystore"}

# Files produced by a script. Hand-editing one means the next run silently
# reverts your change, which is a genuinely bad afternoon.
GENERATED_HINTS = (
    "/.rgignore",
    "/map/",  # narrowed below to schema.sql / *.mmd / derived/
)


def out(message: str) -> None:
    print(message)


def block(message: str) -> "int":
    print(message, file=sys.stderr)
    return 2


def payload() -> dict:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def posix(path: str) -> str:
    return str(path).replace("\\", "/")


def is_secret(path: str) -> bool:
    p = Path(path)
    return p.name in SECRET_NAMES or p.suffix.lower() in SECRET_SUFFIXES


def is_generated(rel: str) -> "str | None":
    """-> the command that regenerates it, or None."""
    r = posix(rel)
    if r.endswith(".rgignore"):
        return "python scripts/sync.py"
    if "/map/" in f"/{r}" or r.startswith("map/"):
        if r.endswith("schema.sql") or r.endswith(".mmd"):
            return "python scripts/snapshot_db.py <area>"
        if "/derived/" in f"/{r}":
            return "the derive: step in project.yaml"
    return None


def project_root(cwd: str) -> "Path | None":
    """Locate the project.

    Its OWN path is the reliable signal: settings.json wires this script as
    <project>/scripts/hooks/guard.py, so the root is two levels up whatever the
    payload says. The payload cwd is only a fallback, because path styles differ
    between shells - a POSIX-style 'cwd' cannot be resolved by Windows Python,
    and letting that decide would silently disable the blocking rules.
    """
    own = Path(__file__).resolve().parent.parent.parent
    if (own / "project.yaml").is_file():
        return own

    try:
        here = Path(cwd or ".").resolve()
    except OSError:
        return None
    for candidate in [here, *here.parents]:
        if (candidate / "project.yaml").is_file():
            return candidate
    return None


def relative(root: Path, path: str) -> "str | None":
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except (ValueError, OSError):
        return None


# ---------------------------------------------------------------------------
# events
# ---------------------------------------------------------------------------


def on_pre_read(root: Path, tool_input: dict) -> int:
    target = tool_input.get("file_path") or tool_input.get("path") or ""
    if not target:
        return 0

    if is_secret(target):
        return block(
            f"Refusing to read {Path(target).name}: it holds credentials.\n"
            "Secrets are never read into a transcript. If you need a value, ask "
            "the human, or invoke an adapter - adapters read .env themselves and "
            "never print it. See docs/adapters.md."
        )

    try:
        size = Path(target).stat().st_size
    except OSError:
        return 0

    if size > READ_BYTES:
        rel = relative(root, target) or Path(target).name
        out(
            f"[guard] {rel} is {size // 1024}KB. Reading it whole costs roughly "
            f"{size // 4000}k tokens, on this turn and every turn after it.\n"
            f"        Cheaper: grep it for what you need, or read its area card "
            f"in map/ if it has one. If you do need the whole file, carry on."
        )
    return 0


def on_pre_write(root: Path, tool_input: dict) -> int:
    target = tool_input.get("file_path") or tool_input.get("path") or ""
    if not target:
        return 0
    rel = relative(root, target)
    if rel is None:
        return 0

    if rel.startswith("systems/"):
        return block(
            f"Refusing to write to {rel}: systems/ is a read-only working "
            "checkout of code this project does not own.\n"
            "It is rebuilt by scripts/sync.py, so the change would be discarded "
            "anyway. Put derived understanding in map/<area>/ instead."
        )

    regen = is_generated(rel)
    if regen:
        return block(
            f"Refusing to hand-edit {rel}: it is generated.\n"
            f"Your change would be silently reverted the next time anything ran. "
            f"Regenerate it instead: {regen}"
        )

    if rel == "STATUS.md":
        body = " ".join(
            str(tool_input.get(k, "")) for k in ("new_string", "content")
        )
        if "Where things stand" in body or "BELOW THIS LINE IS GENERATED" in body:
            return block(
                "Refusing to write the generated half of STATUS.md.\n"
                "Everything below the marker comes from git, the handoffs and the "
                "validators. Run: python scripts/status.py\n"
                "The goal ladder and blockers ABOVE the marker are yours to edit."
            )
    return 0


def on_prompt(root: Path, data: dict) -> int:
    transcript = data.get("transcript_path")
    if not transcript:
        return 0
    try:
        import _transcripts as tx

        context = tx.latest_context(Path(transcript))
    except Exception:
        return 0  # advisory only: fail open, say nothing
    if not context or context < CONTEXT_TOKENS:
        return 0
    out(
        f"[guard] This session is carrying ~{context // 1000}k tokens of context, "
        f"and every further turn pays it again.\n"
        f"        If the current task is nearly done, finish it. If you are "
        f"starting something new, this is the moment to stop:\n"
        f'        python scripts/handoff.py "<topic>"  then begin a fresh session.'
    )
    return 0


def on_pre_compact(root: Path, data: dict) -> int:
    out(
        "[guard] Context is about to be compacted, which means detail is about to "
        "be lost.\n"
        "        Write the handoff FIRST, while the detail still exists:\n"
        '        python scripts/handoff.py "<topic>"'
    )
    return 0


def on_stop(root: Path, data: dict) -> int:
    try:
        import subprocess
        from datetime import date

        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=str(root),
            capture_output=True, text=True,
        )
        changed = [l for l in dirty.stdout.splitlines() if l.strip()]
        if not changed:
            return 0
        today = date.today().isoformat()
        handoffs = root / "context" / "handoffs"
        if handoffs.is_dir() and any(handoffs.glob(f"{today}-*.md")):
            return 0
        out(
            f"[guard] {len(changed)} uncommitted change(s) and no handoff written "
            f"today.\n"
            f"        Twenty minutes of re-explanation next session costs more "
            f"than the two minutes this takes:\n"
            f'        python scripts/handoff.py "<topic>"     (it refreshes '
            f"STATUS.md too)"
        )
    except Exception:
        return 0
    return 0


def main() -> int:
    data = payload()
    event = str(data.get("hook_event_name") or "")
    root = project_root(str(data.get("cwd") or os.getcwd()))
    if root is None:
        return 0  # not one of our projects: no opinions

    tool = str(data.get("tool_name") or "")
    tool_input = data.get("tool_input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}

    if event == "PreToolUse":
        if tool in ("Read", "NotebookRead"):
            return on_pre_read(root, tool_input)
        if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            return on_pre_write(root, tool_input)
        return 0
    if event == "UserPromptSubmit":
        return on_prompt(root, data)
    if event == "PreCompact":
        return on_pre_compact(root, data)
    if event == "Stop":
        return on_stop(root, data)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Rule 1. A guard must never be the reason work stopped.
        sys.exit(0)
