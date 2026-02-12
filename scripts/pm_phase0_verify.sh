#!/usr/bin/env bash
set -euo pipefail

EVD_DIR="docs/planes/pm/_evidence/PM-INV-00.outputs"
INV="docs/planes/pm/PM_PLANE_INVENTORY.md"
GAPS="docs/planes/pm/PM_PLANE_GAPS.md"
LEDGER="docs/planes/pm/PM_PHASE0_CLAIMS_LEDGER.md"

fail() { echo "FAIL: $1" >&2; exit 1; }

[ -d "$EVD_DIR" ] || fail "Missing evidence dir: $EVD_DIR"
count=$(find "$EVD_DIR" -type f ! -name ".gitkeep" | wc -l | tr -d ' ')
[ "$count" -ge 10 ] || fail "Evidence dir too small (found $count files)"

# Inventory + gaps should have at least one :Lx-Ly style citation
grep -qE "L[0-9]+-L[0-9]+" "$INV" || fail "Inventory missing line-range citations"
grep -qE "L[0-9]+-L[0-9]+" "$GAPS" || fail "Gaps missing line-range citations"

# Claims ledger must have citations on all Verified lines (simple heuristic)
awk '
  BEGIN{in_verified=0}
  /^## Verified/{in_verified=1; next}
  /^## /{in_verified=0}
  in_verified==1 && $0 ~ /^[0-9]+\)/ {
    if ($0 !~ /L[0-9]+-L[0-9]+/) { print "Missing citation:", NR ":" $0; bad=1 }
  }
  END{exit(bad?1:0)}
' "$LEDGER" || fail "Claims ledger verified claims missing citations"

echo "OK: PM Phase 0 verification passed"
