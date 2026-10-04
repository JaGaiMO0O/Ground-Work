#!/usr/bin/env bash
# Placeholder `capture` adapter. It does nothing, and says so.
#
# Declared in project.yaml as:   adapters: { capture: _stub }
#
# Replace it: copy scripts/adapters/capture/rest.py if the system speaks HTTP.
# The contract is in docs/adapters.md.
#
# If the system has NO observable boundary - Oracle Forms, a batch-only job, a
# desktop client on a proprietary protocol - do not write an adapter at all.
# Declare `capture: none` and follow context/recipes/no-boundary-contract.md.
# That is the supported path, not a workaround.

verb="${1:-?}"
echo "  [_stub] no 'capture' adapter implemented for ${AREA_NAME:-?} (verb: ${verb})" >&2
echo "  [_stub] Either write one (docs/adapters.md) or declare 'capture: none'" >&2
echo "  [_stub] and use context/recipes/no-boundary-contract.md" >&2
exit 3
