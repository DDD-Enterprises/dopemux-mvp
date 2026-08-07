# Capability Preflight & Git Topology Baseline (R2A Repair)

- **Repository Root**: `/private/tmp/wt-1205`
- **S0 origin/main Commit**: `33d6c353023ecc3aa6331ab39f4f076ae3ca1fda`
- **S1 origin/main Commit**: `33d6c353023ecc3aa6331ab39f4f076ae3ca1fda`
- **Main Branch Drift**: `False`
- **Portfolio PR Drift Classified**: `True` (NO_MATERIAL_EFFECT)
- **Authenticated GitHub Connector**: `PASS`
- **Open PR Count**: `50`
- **Actual Pair Records Generated**: `1225` (Expected: `1225`)
- **All 49 Other PR Changed Files Exactly Reconciled**: `True`
- **PR #1123 File Coverage**: `PARTIAL (16205/16206, Quarantined)`
- **Mandatory Stack Regression Fixture (#1136 -> #1183)**: `True`
- **No Path-Only Independence Classifications**: `True`

## Collection Invariants Verification
1. GraphQL paginated file extraction + Git fallback with PR #1123 path quarantine.
2. Per-PR Git topology computed against origin/main and actual base ref.
3. Pair topology matrix computed for all 1225 pairs with multi-axis ancestry, stack, path, tree, patch identity, and merge_compatibility fields.
4. S1 PR inventory drift re-harvested and verified (`moved_heads=[]`).
5. Relative path manifest and byte-for-byte deterministic ZIP package built.
