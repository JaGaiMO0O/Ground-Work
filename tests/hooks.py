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
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GUARD = REPO / "scripts" / "hooks" / "guard.py"
sys.path.insert(0, str(REPO / "scripts"))
import _transcripts  # noqa: E402
TMP = Path(tempfile.gettempdir()) / f"guard-tests-{os.getpid()}"

BLOCK, WARN, SILENT = "block", "warn", "silent"

# How Claude Code names a project's folder under ~/.claude/projects. A wrong slug
# means usage.py finds no transcripts and reports "no telemetry", not an error.
SLUG_CASES = [
    (r"C:\Users\me\Desktop\RedKeys\Name_Screening",
     "C--Users-me-Desktop-RedKeys-Name-Screening"),
    (r"C:\Users\me\Desktop\Legacy Modernization",
     "C--Users-me-Desktop-Legacy-Modernization"),
    ("/home/me/my_proj (copy)", "-home-me-my-proj--copy-"),
]


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


def hook_command(event: str) -> str:
    """The command Claude Code actually runs - read from settings, never copied."""
    settings = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    return settings["hooks"][event][0]["hooks"][0]["command"]


def find_bash():
    """-> (path, None) or (None, why not). The shell Claude Code itself uses.

    On Windows that is Git Bash. Plain `bash` there often resolves to
    System32\\bash.exe, the WSL launcher - never fall back to it.
    """
    override = os.environ.get("CLAUDE_CODE_GIT_BASH_PATH")
    if override:
        return override, None
    if os.name != "nt":
        bash = shutil.which("bash")
        if bash:
            return bash, None
        return None, "bash not on PATH - Claude Code runs hooks through a POSIX shell"
    git = shutil.which("git")
    if git:
        # git.exe sits in Git\cmd, Git\bin or Git\mingw64\bin, by version.
        here = Path(git).resolve().parent
        for d in [here, *here.parents][:4]:
            if (d / "bin" / "bash.exe").is_file():
                return str(d / "bin" / "bash.exe"), None
    return None, ("no Git Bash found - Claude Code needs Git for Windows "
                  "(or CLAUDE_CODE_GIT_BASH_PATH) to run hooks")


def fire_hook(event: str, payload: dict):
    """-> (exit code, bash, None) or (None, None, why it could not run).

    Runs the real wiring, not just guard.py: a hook that cannot find Python
    fails open, and the guard tests above would never notice.
    """
    bash, why = find_bash()
    if not bash:
        return None, None, why
    proc = subprocess.run(
        [bash, "-c", hook_command(event)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(REPO),
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(REPO)},
    )
    return proc.returncode, bash, None


def nuke(path: Path):
    """Same pattern as tests/invariants.py: TMP is per process, so remove it."""

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

    # The real hook command from settings.json, judged by exit code: 2 blocks,
    # 0 allows. Anything else means the wiring broke, whichever way it fails.
    wiring = [
        ("hook wiring: read .env",       pre("Read", REPO / ".env"), 2),
        ("hook wiring: read README.md",  pre("Read", REPO / "README.md"), 0),
    ]

    failures = 0
    print(f"{'case':34} {'got':>7} {'want':>7}  result")
    print("-" * 66)
    for name, payload, want in cases:
        got = fire(payload)
        good = got == want
        failures += 0 if good else 1
        print(f"{name:34} {got:>7} {want:>7}  {'ok' if good else 'FAILED'}")
    for name, payload, want in wiring:
        code, bash, why = fire_hook("PreToolUse", payload)
        good = code == want
        failures += 0 if good else 1
        got = "n/a" if code is None else f"exit {code}"
        print(f"{name:34} {got:>7} {'exit ' + str(want):>7}  {'ok' if good else 'FAILED'}"
              f"  [bash: {bash or 'none'}]")
        if why:
            print(f"  {why}")
    for given, want in SLUG_CASES:
        got = _transcripts._slug(Path(given))
        good = got == want
        failures += 0 if good else 1
        print(f"{'slug: ' + given:34} {got:>7} {want:>7}  {'ok' if good else 'FAILED'}")

    total = len(cases) + len(wiring) + len(SLUG_CASES)
    print("-" * 66)
    print(f"{total - failures}/{total} passed")
    if not long_session:
        print("note: no local transcripts, so the context-nudge cases were skipped")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        code = main()
    finally:
        nuke(TMP)
    sys.exit(code)
