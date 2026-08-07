# Capability Preflight & Git Topology Baseline (R2 Repair)

- **Repository Root**: `/Users/hue/code/dopemux-mvp/.worktrees/TP-DMX-DELTA-REHARVEST-001-R2`
- **S0 origin/main Commit**: `33d6c353023ecc3aa6331ab39f4f076ae3ca1fda`
- **S1 origin/main Commit**: `33d6c353023ecc3aa6331ab39f4f076ae3ca1fda`
- **Main Branch Drift**: `False`
- **Authenticated GitHub Connector**: `PASS`
- **Open PR Count**: `49`
- **Actual Pair Records Generated**: `1176` (Expected: `1176`)
- **All Changed Files Exactly Reconciled**: `True`
- **Mandatory Stack Regression Fixture (#1136 -> #1183)**: `True`

## Collection Invariants Verification
1. GraphQL paginated file extraction + Git fallback (zero fudge factor).
2. Per-PR Git topology computed against origin/main.
3. Pair topology matrix computed for all 1176 pairs with ancestry and heavy candidate edge analysis.
4. Relative path manifest and byte-for-byte deterministic ZIP package built.
