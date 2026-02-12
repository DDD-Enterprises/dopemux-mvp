#!/usr/bin/env bash
set -euo pipefail

EVD_DIR="docs/planes/pm/_evidence/PM-FRIC-01.outputs"
TELEM_EVD_DIR="docs/planes/pm/_evidence/PM-TELEM-01.outputs"
FRIC="docs/planes/pm/PM_FRICTION_MAP.md"
SNSA="docs/planes/pm/SIGNAL_VS_NOISE_ANALYSIS.md"

fail() { echo "FAIL: $1" >&2; exit 1; }

[ -d "$EVD_DIR" ] || fail "Missing evidence dir: $EVD_DIR"
count=$(find "$EVD_DIR" -type f | wc -l | tr -d ' ')
[ "$count" -ge 5 ] || fail "Phase 1 evidence dir too small (found $count files)"
[ -d "$TELEM_EVD_DIR" ] || fail "Missing telemetry evidence dir: $TELEM_EVD_DIR"
telemetry_count=$(find "$TELEM_EVD_DIR" -type f | wc -l | tr -d ' ')
[ "$telemetry_count" -ge 5 ] || fail "Telemetry evidence dir too small (found $telemetry_count files)"

grep -qE "L[0-9]+-L[0-9]+" "$FRIC" || fail "Friction map missing line-range citations"
grep -qE "L[0-9]+-L[0-9]+" "$SNSA" || fail "Signal/noise doc missing line-range citations"
grep -q "PM-TELEM-01.outputs" "$SNSA" || fail "Signal/noise doc missing telemetry evidence references"

echo "OK: PM Phase 1 verification passed"
