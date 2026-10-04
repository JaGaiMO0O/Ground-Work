#!/usr/bin/env python3
"""new_card.py - start an area card, prefilled from project.yaml.

    python scripts/new_card.py api

Creates map/<area>/CARD.md from the template with the location, stack, owner and
date already filled in. Everything else is yours.

Read context/recipes/survey-area.md before filling it in. Surveying is a
dedicated, disposable session and it is paid once.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

import _lib as lib
from _lib import ROOT

TEMPLATE_DIR = lib.MAP_DIR / "_TEMPLATE"


def source_line(area: lib.Area) -> str:
    """The one header field that locates this area. Which one depends on kind."""
    if area.kind == "repo":
        return f"Repo: {area.url or '<url>'} @ {area.ref or '<ref>'}"
    if area.kind == "database":
        owners = ", ".join(str(o) for o in area.schema_owners) or "<schema owners>"
        return f"Schema: {owners}"
    if area.kind == "fileshare":
        return "Location: <path or share>"
    return f"Path: {', '.join(str(p) for p in area.paths) or '<paths>'}"


def prefill(text: str, area: lib.Area) -> str:
    today = date.today().isoformat()
    stack = ", ".join(str(v) for v in (area.stack or {}).values())

    text = text.replace("# Area Card: <name>", f"# Area Card: {area.name}")
    text = text.replace("# Seams: <name>", f"# Seams: {area.name}")
    text = text.replace(
        "Path: <where this area lives>  |  Surveyed: <date>  |  Owner: <who>",
        f"{source_line(area)}  |  Surveyed: {today}"
        f"  |  Owner: {area.owner or '<who>'}",
    )
    if stack:
        text = text.replace("Stack:", f"Stack: {stack}", 1)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("area")
    parser.add_argument("--force", action="store_true",
                        help="overwrite an existing card")
    args = parser.parse_args()

    project = lib.load_project()
    area = project.require(args.area)

    if not TEMPLATE_DIR.exists():
        return lib.die(f"{TEMPLATE_DIR} is missing - the template has been damaged")

    area.card_dir.mkdir(parents=True, exist_ok=True)
    written = []

    # The card is core. A profile may add more templates alongside it - the
    # legacy profile adds seams.md - so copy whatever the template dir holds.
    for source in sorted(TEMPLATE_DIR.glob("*.md")):
        target = area.card_dir / source.name
        if target.exists() and not args.force:
            lib.warn(f"{target.relative_to(ROOT).as_posix()} already exists - kept")
            continue
        target.write_text(
            prefill(source.read_text(encoding="utf-8"), area), encoding="utf-8"
        )
        written.append(target.relative_to(ROOT).as_posix())

    for path in written:
        lib.ok(f"wrote {path}")

    if not area.survey:
        lib.info(
            f"\n  {area.name} has 'survey: false', so this is a partial card. Fill only\n"
            "  what you know, with citations, and add landmines as tasks teach them.\n"
            "  A full survey is for the area's third task."
        )

    lib.info(
        "\n  A full survey follows context/recipes/survey-area.md and starts by\n"
        "  asking a human."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
