#!/usr/bin/env python3
"""test_golden.py - golden-master equivalence tests.

Replays the fixtures recorded by capture.py against the replacement and reports
where behaviour differs. This is what lets you claim the new thing does what the
old thing did, rather than hoping so.

Named test_golden.py rather than test.py so pytest does not try to collect it.
The Appendix E name `test.sh` still works as a shim.

    python scripts/test_golden.py                  # all areas with a test adapter
    python scripts/test_golden.py billing-legacy
"""

from __future__ import annotations

import argparse
import sys

import _lib as lib
from _lib import ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("areas", nargs="*")
    parser.add_argument("--target", help="base URL or endpoint of the replacement")
    args = parser.parse_args()

    project = lib.load_project()
    targets = (
        [project.require(name) for name in args.areas]
        if args.areas
        else [s for s in project.areas if (s.adapters or {}).get("test")]
    )
    if not targets:
        lib.warn("no area declares a 'test' adapter - nothing to replay")
        return 0

    status = 0
    for area in targets:
        fixtures = ROOT / "integration" / "fixtures" / area.name
        if not fixtures.exists():
            lib.warn(
                f"{area.name}: no fixtures at {fixtures.relative_to(ROOT).as_posix()}"
            )
            lib.info(f"       python scripts/capture.py {area.name} fixtures")
            continue
        extra = ["--fixtures", str(fixtures)]
        if args.target:
            extra += ["--target", args.target]
        code = lib.run_adapter(area, "test", "run", extra=extra)
        status = max(status, lib.adapter_status(code))
    return status


if __name__ == "__main__":
    sys.exit(main())
