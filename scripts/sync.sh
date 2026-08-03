#!/usr/bin/env sh
# Shim. The playbook's Appendix E calls this sync.sh; the implementation is
# sync.py. Kept so the documented interface stays true on any platform.
PY=$(command -v python3 || command -v python) || {
  echo "python 3 is required but was not found on PATH" >&2; exit 1; }
exec "$PY" "$(dirname "$0")/sync.py" "$@"
