#!/usr/bin/env sh
# Shim. The playbook's Appendix E calls this init.sh; the implementation is
# init.py. Kept so the documented interface stays true on any platform.
PY=$(command -v python || command -v python3) || {
  echo "python 3 is required but was not found on PATH" >&2; exit 1; }
exec "$PY" "$(dirname "$0")/init.py" "$@"
