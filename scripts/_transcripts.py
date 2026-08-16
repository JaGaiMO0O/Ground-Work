"""Reading Claude Code session transcripts.

THIS IS THE ONLY FILE THAT KNOWS THE TRANSCRIPT FORMAT.

That is deliberate. The format under ~/.claude/projects/*.jsonl is internal to
Claude Code - not a published API - and it can change without notice. It is the
one dependency in this repo that cannot be pinned. Isolating it here means a
format change is a single-file fix rather than an archaeology exercise.

Three rules this module must keep:

  1. NEVER report zeros on a parse failure. A budget tool that silently says
     "0 tokens" reads as good news, which is worse than saying nothing. Every
     metric carries an availability flag, and the caller must honour it.
  2. Degrade per metric. If `usage` still parses but tool calls have moved,
     cache and context reporting keep working and only tool analysis goes quiet.
  3. Never raise. Callers are advisory tools; a broken transcript must not take
     down anything else.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# schema touch points - everything version-specific lives in this block
# ---------------------------------------------------------------------------

PROJECTS_DIR = Path(os.path.expanduser("~")) / ".claude" / "projects"

_USAGE_KEYS = {
    "input": "input_tokens",
    "output": "output_tokens",
    "cache_read": "cache_read_input_tokens",
    "cache_write": "cache_creation_input_tokens",
}
_ENTRY_MESSAGE = "message"
_ENTRY_SIDECHAIN = "isSidechain"
_ENTRY_CWD = "cwd"
_ENTRY_SESSION = "sessionId"
_ENTRY_TIMESTAMP = "timestamp"
_CONTENT_TOOL_USE = "tool_use"

# Tool names, by what they cost you. Orientation is the spend on working out
# where you are; work is the spend on changing something.
ORIENTATION_TOOLS = {
    "Read", "Grep", "Glob", "LS", "NotebookRead", "WebFetch", "WebSearch",
}
WORK_TOOLS = {"Edit", "MultiEdit", "Write", "NotebookEdit", "Bash"}


def native_path(recorded: str) -> Path:
    """Turn a path as recorded in a transcript into one this OS can open.

    A session run through git-bash records POSIX paths - `/c/Users/...`. On
    Windows those resolve to `C:\\c\\Users\\...`, which does not exist, so every
    file lookup silently fails and anything derived from it degrades to
    "unknown". Same trap as a hook payload carrying a POSIX `cwd`.
    """
    text = str(recorded)
    if os.name == "nt":
        match = re.match(r"^/([a-zA-Z])/(.*)$", text)
        if match:
            text = f"{match.group(1).upper()}:/{match.group(2)}"
    return Path(text)


def _slug(path: Path) -> str:
    """~/.claude/projects uses a flattened form of the working directory."""
    text = str(path.resolve())
    for char in (":", "\\", "/", " ", "."):
        text = text.replace(char, "-")
    return text


# ---------------------------------------------------------------------------
# model
# ---------------------------------------------------------------------------


@dataclass
class Turn:
    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0
    sidechain: bool = False

    @property
    def context(self) -> int:
        """What was carried into this turn - the number that grows."""
        return self.input + self.cache_read + self.cache_write


@dataclass
class Session:
    id: str
    path: Path
    project: str
    turns: "list[Turn]" = field(default_factory=list)
    tools: Counter = field(default_factory=Counter)
    reads: "list[str]" = field(default_factory=list)
    first_ts: str = ""
    last_ts: str = ""

    @property
    def output(self) -> int:
        return sum(t.output for t in self.turns)

    @property
    def cache_read(self) -> int:
        return sum(t.cache_read for t in self.turns)

    @property
    def cache_write(self) -> int:
        return sum(t.cache_write for t in self.turns)

    @property
    def main_turns(self) -> "list[Turn]":
        """Main-loop turns only. Subagent turns have their own context and would
        distort the growth curve."""
        return [t for t in self.turns if not t.sidechain]

    @property
    def baseline_context(self) -> int:
        """Context carried on the first turn: system prompt, instructions and
        every enabled tool definition, before any work happened."""
        main = self.main_turns
        return main[0].context if main else 0

    @property
    def peak_context(self) -> int:
        main = self.main_turns
        return max((t.context for t in main), default=0)


@dataclass
class Telemetry:
    sessions: "list[Session]" = field(default_factory=list)
    have_usage: bool = False
    have_tools: bool = False
    scanned_files: int = 0
    bad_lines: int = 0
    problems: "list[str]" = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.sessions)


# ---------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------


def project_dirs_for(cwd: Path) -> "list[Path]":
    """Transcript directories belonging to `cwd`.

    Tries the flattened-name convention first, then falls back to reading the
    `cwd` recorded inside each transcript - which survives a change to how the
    directory names are built.
    """
    if not PROJECTS_DIR.is_dir():
        return []

    exact = PROJECTS_DIR / _slug(cwd)
    if exact.is_dir():
        return [exact]

    wanted = str(cwd.resolve()).lower()
    found = []
    for candidate in sorted(PROJECTS_DIR.iterdir()):
        if not candidate.is_dir():
            continue
        for jsonl in candidate.glob("*.jsonl"):
            recorded = _peek_cwd(jsonl)
            if recorded and recorded.lower() == wanted:
                found.append(candidate)
            break
    return found


def _peek_cwd(path: Path) -> "str | None":
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for _ in range(40):
                line = handle.readline()
                if not line:
                    return None
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict) and entry.get(_ENTRY_CWD):
                    return str(entry[_ENTRY_CWD])
    except OSError:
        return None
    return None


def read_dirs(dirs: "list[Path]") -> Telemetry:
    """Parse every transcript in `dirs`. Never raises."""
    tel = Telemetry()
    if not dirs:
        tel.problems.append("no transcript directory found for this project")
        return tel

    for directory in dirs:
        for jsonl in sorted(directory.glob("*.jsonl")):
            session = _read_session(jsonl, directory.name, tel)
            if session is not None and (session.turns or session.tools):
                tel.sessions.append(session)
            tel.scanned_files += 1

    if not tel.sessions:
        tel.problems.append(
            "transcripts were found but nothing could be read from them - "
            "the format may have changed"
        )
    return tel


def _read_session(path: Path, project: str, tel: Telemetry) -> "Session | None":
    session = Session(id=path.stem, path=path, project=project)
    try:
        handle = path.open(encoding="utf-8", errors="replace")
    except OSError:
        tel.problems.append(f"could not open {path.name}")
        return None

    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                tel.bad_lines += 1
                continue
            if not isinstance(entry, dict):
                tel.bad_lines += 1
                continue

            stamp = entry.get(_ENTRY_TIMESTAMP)
            if stamp:
                session.first_ts = session.first_ts or str(stamp)
                session.last_ts = str(stamp)

            message = entry.get(_ENTRY_MESSAGE)
            if not isinstance(message, dict):
                continue

            usage = message.get("usage")
            if isinstance(usage, dict):
                turn = Turn(sidechain=bool(entry.get(_ENTRY_SIDECHAIN)))
                got_any = False
                for attr, key in _USAGE_KEYS.items():
                    value = usage.get(key)
                    if isinstance(value, (int, float)):
                        setattr(turn, attr, int(value))
                        got_any = True
                if got_any:
                    session.turns.append(turn)
                    tel.have_usage = True

            content = message.get("content")
            if isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != _CONTENT_TOOL_USE:
                        continue
                    name = block.get("name")
                    if not name:
                        continue
                    session.tools[str(name)] += 1
                    tel.have_tools = True
                    if str(name) in ("Read", "NotebookRead"):
                        target = (block.get("input") or {}).get("file_path")
                        if target:
                            session.reads.append(str(target))
    return session


def latest_context(transcript: Path, tail_bytes: int = 400_000) -> "int | None":
    """Context size carried on the most recent main-loop turn, or None.

    Reads only the tail of the file. A hook runs on every prompt, so it must not
    walk a 9 MB transcript to answer one question.
    """
    try:
        size = transcript.stat().st_size
        with transcript.open("rb") as handle:
            if size > tail_bytes:
                handle.seek(size - tail_bytes)
                handle.readline()  # discard the partial line
            raw = handle.read().decode("utf-8", errors="replace")
    except OSError:
        return None

    for line in reversed(raw.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict) or entry.get(_ENTRY_SIDECHAIN):
            continue
        message = entry.get(_ENTRY_MESSAGE)
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        total = 0
        for key in ("input_tokens", "cache_read_input_tokens",
                    "cache_creation_input_tokens"):
            value = usage.get(key)
            if isinstance(value, (int, float)):
                total += int(value)
        if total:
            return total
    return None


def read_for(cwd: Path) -> Telemetry:
    return read_dirs(project_dirs_for(cwd))


def read_all() -> Telemetry:
    if not PROJECTS_DIR.is_dir():
        tel = Telemetry()
        tel.problems.append(f"{PROJECTS_DIR} does not exist")
        return tel
    return read_dirs([d for d in sorted(PROJECTS_DIR.iterdir()) if d.is_dir()])
