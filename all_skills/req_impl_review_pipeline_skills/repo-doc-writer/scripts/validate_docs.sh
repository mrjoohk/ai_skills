#!/bin/bash
# validate_docs.sh — checks that required docs/ai/ files exist and are non-empty

ROOT=${1:-.}
DOCS="$ROOT/docs/ai"
PASS=0
FAIL=0

check() {
  if [ -s "$1" ]; then
    echo "  ✓ $1"
    PASS=$((PASS+1))
  else
    echo "  ✗ MISSING or EMPTY: $1"
    FAIL=$((FAIL+1))
  fi
}

echo "=== docs/ai validation ==="
check "$DOCS/overview.md"
check "$DOCS/architecture.md"

TASKS=$(find "$DOCS/tasks" -name "*.md" 2>/dev/null | wc -l)
echo "  Task files found: $TASKS"

echo ""
echo "Result: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
