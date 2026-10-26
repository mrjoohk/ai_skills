#!/bin/bash
# Compatibility entrypoint. First positional argument remains project root.
set -euo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=${1:-.}
if [ "$#" -gt 0 ]; then shift; fi
exec "${PYTHON:-python3}" "$SCRIPT_DIR/validate_docs.py" --root "$ROOT" "$@"
