#!/usr/bin/env bash
set -euo pipefail

EVD_DIR="docs/planes/pm/_evidence/PM-FRIC-01.outputs"
FRIC="docs/planes/pm/PM_FRICTION_MAP.md"
SNSA="docs/planes/pm/SIGNAL_VS_NOISE_ANALYSIS.md"

fail() { echo "FAIL: $1" >&2; exit 1; }

[ -d "$EVD_DIR" ] || fail "Missing evidence dir: $EVD_DIR"
count=$(find "$EVD_DIR" -type f | wc -l | tr -d ' ')
[ "$count" -ge 5 ] || fail "Phase 1 evidence dir too small (found $count files)"

grep -qE "L[0-9]+-L[0-9]+" "$FRIC" || fail "Friction map missing line-range citations"
grep -qE "L[0-9]+-L[0-9]+" "$SNSA" || fail "Signal/noise doc missing line-range citations"

echo "OK: PM Phase 1 verification passed"
