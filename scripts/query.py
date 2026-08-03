#!/usr/bin/env python3
"""query.py - read-only parameterized queries against a declared area.

This exists so you do not need a database MCP server. A DB server costs tokens
on EVERY turn of every conversation whether or not you query it; this script
costs nothing until it is called.

    python scripts/query.py billing-legacy "SELECT count(*) FROM invoice"
    python scripts/query.py billing-legacy --file queries/open-invoices.sql
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import _lib as lib

# Defence in depth. The adapter must enforce read-only too, but a typo should
# never make it as far as the database.
READ_ONLY = re.compile(r"^\s*(?:--[^\n]*\n|/\*.*?\*/|\s)*(SELECT|WITH)\b",
                       re.I | re.S)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("area")
    parser.add_argument("sql", nargs="?", help="SQL text (or use --file)")
    parser.add_argument("--file", help="read the statement from a file")
    parser.add_argument("--param", action="append", default=[], metavar="K=V",
                        help="bind variable, repeatable")
    parser.add_argument("--out", help="write results here instead of stdout")
    args = parser.parse_args()

    if not args.sql and not args.file:
        return lib.die("give a SQL statement, or --file")

    statement = args.sql or Path(args.file).read_text(encoding="utf-8")
    if not READ_ONLY.match(statement):
        return lib.die(
            "refusing to run: only SELECT and WITH statements are permitted.\n"
            "     Agents get a read-only role and a read-only tool. Schema "
            "changes go through migrations/."
        )

    project = lib.load_project()
    area = project.require(args.area)

    extra = ["--sql", statement]
    for pair in args.param:
        extra += ["--param", pair]

    code = lib.run_adapter(
        area, "db", "query", extra=extra, out=Path(args.out) if args.out else None
    )
    return lib.adapter_status(code)


if __name__ == "__main__":
    sys.exit(main())
