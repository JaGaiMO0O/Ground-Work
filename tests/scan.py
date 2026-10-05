"""Prove the secret scan's regex fallback finds secrets and ignores code.

    python tests/scan.py

The scan is a gate, and a noisy gate gets switched off. So two properties are
tested, one file per case:

  * true positives still fire - the expected rule is among those returned
  * code and placeholders do not - the result is exactly empty

Each case writes a one-line .py file into a temp directory named with the PID,
so parallel runs never share one, and calls scan.regex_scan on it directly.
A case may name its scan root and file, to test where the project sits on disk.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import scan  # noqa: E402
TMP = Path(tempfile.gettempdir()) / f"scan-tests-{os.getpid()}"

NOTHING = None

CASES = [
    # --- must fire ------------------------------------------------------------
    ("unquoted property secret",          "DB_PASSWORD=s3cr3tValue9",
     "password-property"),
    # Both password-assignment and password-property fire here today, hence inclusion.
    ("quoted assignment secret",          'password = "hunter2xyz"',
     "password-assignment"),
    # --- must stay quiet ------------------------------------------------------
    ("compile call is not a secret",      "_NUMERIC_TOKEN = re.compile(", NOTHING),
    ("env lookup is not a secret",        'api_key = os.environ.get("API_KEY")', NOTHING),
    ("function call is not a secret",     "password = getpass()", NOTHING),
    ("placeholder is not a secret",       "PASSWORD=changeme", NOTHING),
    # --- skip list applies inside the project only: (scan root, file) --------
    ("repo under a build folder",         "DB_PASSWORD=s3cr3tValue9",
     "password-property", ("build/repo", "a.py")),
    ("build folder inside repo skipped",  "DB_PASSWORD=s3cr3tValue9", NOTHING,
     ("repo", "build/a.py")),
]


def rules_for(index: int, line: str, root: str = ".", file: str = "case.py") -> "list[str]":
    scan_root = TMP / f"case-{index}" / root
    target = scan_root / file
    target.parent.mkdir(parents=True)
    target.write_text(line + "\n", encoding="utf-8")
    return sorted(f["rule"] for f in scan.regex_scan(scan_root))


def main() -> int:
    failures = 0
    print(f"{'case':34} {'want':>20}  result")
    print("-" * 66)
    for index, (name, line, want, *where) in enumerate(CASES):
        got = rules_for(index, line, *(where[0] if where else ()))
        good = (not got) if want is NOTHING else (bool(got) and want in got)
        failures += 0 if good else 1
        print(f"{name:34} {want or 'nothing':>20}  {'ok' if good else 'FAILED'}")
        if not good:
            print(f"  got: {', '.join(got) or 'nothing'}")
    print("-" * 66)
    print(f"{len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        code = main()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    sys.exit(code)
