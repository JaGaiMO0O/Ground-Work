#!/usr/bin/env python3
"""snapshot_db.py - regenerate schema.sql and erd.mmd for a area.

Derive, don't describe: a generated schema snapshot beats a prose description
on precision AND on cost, and it never goes stale in the way prose does.

Dispatches to the area's declared `db` adapter. See docs/adapters.md.

    python scripts/snapshot_db.py                    # every area with a db adapter
    python scripts/snapshot_db.py billing-legacy
    python scripts/snapshot_db.py billing-legacy --schema-only
"""

from __future__ import annotations

import argparse
import sys

import _lib as lib


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("areas", nargs="*",
                        help="areas to snapshot (default: all with a db adapter)")
    parser.add_argument("--schema-only", action="store_true")
    parser.add_argument("--erd-only", action="store_true")
    args = parser.parse_args()

    project = lib.load_project()
    targets = (
        [project.require(name) for name in args.areas]
        if args.areas
        else [s for s in project.areas if (s.adapters or {}).get("db")]
    )
    if not targets:
        lib.warn("no area declares a 'db' adapter - nothing to snapshot")
        return 0

    status = 0
    for area in targets:
        area.card_dir.mkdir(parents=True, exist_ok=True)
        if not args.erd_only:
            code = lib.run_adapter(
                area, "db", "schema", out=area.card_dir / "schema.sql"
            )
            status = max(status, lib.adapter_status(code))
        if not args.schema_only:
            code = lib.run_adapter(
                area, "db", "erd", out=area.card_dir / "erd.mmd"
            )
            status = max(status, lib.adapter_status(code))
    return status


if __name__ == "__main__":
    sys.exit(main())
