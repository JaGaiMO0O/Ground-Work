#!/usr/bin/env bash
# Placeholder `db` adapter. It does nothing, and says so.
#
# Declared in project.yaml as:   adapters: { db: _stub }
#
# Replace it: copy scripts/adapters/db/postgres.sh (the closest working
# reference), rename it for your engine, and point the system at it.
# The contract - verbs, environment, exit codes - is in docs/adapters.md.
#
# This ships as a stub rather than as an untested implementation on purpose.
# A stub tells you it is a stub; a broken adapter tells you your schema is empty.

verb="${1:-?}"
echo "  [_stub] no 'db' adapter implemented for ${AREA_NAME:-?} (verb: ${verb})" >&2
echo "  [_stub] Write one: copy scripts/adapters/db/postgres.sh - docs/adapters.md" >&2
exit 3
