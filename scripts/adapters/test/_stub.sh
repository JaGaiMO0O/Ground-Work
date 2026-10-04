#!/usr/bin/env bash
# Placeholder `test` adapter. It does nothing, and says so.
#
# Declared in project.yaml as:   adapters: { test: _stub }
#
# A `test` adapter replays the fixtures recorded by capture.py against the
# replacement and reports where behaviour differs. Without one you cannot claim
# behavioural equivalence - you can only claim the new code runs.
#
# The contract is in docs/adapters.md. Fixtures live in
# integration/fixtures/<system>/.

verb="${1:-?}"
echo "  [_stub] no 'test' adapter implemented for ${AREA_NAME:-?} (verb: ${verb})" >&2
echo "  [_stub] Golden-master replay is what proves equivalence - docs/adapters.md" >&2
exit 3
