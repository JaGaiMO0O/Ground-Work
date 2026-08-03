#!/usr/bin/env python3
"""handoff.py - write the session handoff.

    python scripts/handoff.py "invoice export"

~200 tokens that replace twenty minutes of re-explanation next session. Write
one at the end of any session that will be continued.

Handoffs are dated so they sort, because they double as the project log a new
joiner reads chronologically.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date

import _lib as lib
from _lib import ROOT

FOLDER = ROOT / "context" / "handoffs"
TEMPLATE = FOLDER / "_TEMPLATE.md"


def slugify(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return slug or "session"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("topic", help="short topic, e.g. 'invoice export'")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    FOLDER.mkdir(parents=True, exist_ok=True)
    target = FOLDER / f"{args.date}-{slugify(args.topic)}.md"

    if target.exists():
        lib.warn(f"{target.relative_to(ROOT).as_posix()} already exists")
        return 0

    body = (
        TEMPLATE.read_text(encoding="utf-8")
        if TEMPLATE.exists()
        else "# Handoff <date> - <topic>\n\nGoal:\nDone:\nOpen:\n"
             "Key files:\nGotcha:\nNext:\n"
    )
    body = body.replace("<date>", args.date).replace("<topic>", args.topic)
    target.write_text(body, encoding="utf-8")

    lib.ok(f"wrote {target.relative_to(ROOT).as_posix()}")
    lib.info(
        "       Fill 'Gotcha' honestly - it is where the thing that cost you an\n"
        "       hour goes, so it costs the next person nothing."
    )

    # Refresh the state snapshot in the same step. Asking an untrained user to
    # adopt a second habit will not work; one more line inside a habit they
    # already have will.
    import subprocess

    status = ROOT / "scripts" / "status.py"
    if status.exists():
        subprocess.run([sys.executable, str(status)], cwd=str(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
