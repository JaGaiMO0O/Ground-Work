#!/usr/bin/env python3
"""capture.py - derive a contract from observed traffic, not from documentation.

For areas this age the documentation lies and formal specs do not exist.
Watching the running area is both cheaper and more trustworthy than reading
it. One capture pass yields three things:

  1. a contract grounded in observed reality rather than aspiration
  2. golden-master fixtures, so you can prove equivalence when you replace it
  3. evidence of what is ACTUALLY used - which routinely shrinks scope

    python scripts/capture.py billing-legacy record --hours 24
    python scripts/capture.py billing-legacy contract
    python scripts/capture.py billing-legacy fixtures

If a area has no observable boundary - Oracle Forms, batch-only jobs - the
adapter exits 3 and you should follow context/recipes/no-boundary-contract.md
instead. That is a normal outcome, not a failure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _lib as lib
from _lib import ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("area")
    parser.add_argument("verb", nargs="?", default="record",
                        choices=["record", "contract", "fixtures"])
    parser.add_argument("--hours", type=float, default=24.0,
                        help="recording window (record only)")
    parser.add_argument("--port", type=int, default=8888,
                        help="local port the recorder listens on")
    parser.add_argument("--out", help="override the default output path")
    args = parser.parse_args()

    project = lib.load_project()
    area = project.require(args.area)

    fixtures = ROOT / "integration" / "fixtures" / area.name
    defaults = {
        "record": fixtures / "raw",
        "contract": ROOT / "integration" / "contracts" / f"{area.name}.v0.yaml",
        "fixtures": fixtures,
    }
    out = Path(args.out) if args.out else defaults[args.verb]

    extra: list = []
    if args.verb == "record":
        extra = ["--hours", str(args.hours), "--port", str(args.port)]

    code = lib.run_adapter(area, "capture", args.verb, extra=extra, out=out)

    if code == 3 and args.verb in ("record", "contract"):
        lib.info(
            "       This area has no boundary to record. Use the fallback:\n"
            "       context/recipes/no-boundary-contract.md"
        )
    return lib.adapter_status(code)


if __name__ == "__main__":
    sys.exit(main())
