# CCAR-002 Command Log

## Original C1 implementation
- Builder v1.0.0 catalog generation and 21 focused tests (historical).

## CCAR-002R R1 · Portability repair (2026-08-02/03)
- `python3 scripts/commandcode_router/build_normalized_catalog.py --repo-root <wt>` → exit 0
- `python3 scripts/commandcode_router/build_normalized_catalog.py --check --repo-root <wt>` → exit 0
- `python3 -m pytest tests/commandcode_router/test_normalized_catalog.py -v` → 24 passed
- Dual-worktree byte-identical catalog test: PASS (fixed generated_at)
- `meta.source_manifest` = `proof/CCAR-002/SOURCE_MANIFEST.json` (repo-relative)
- Repo-root resolution: git toplevel / markers / optional `--repo-root` (validated)
- Source agent/persona bytes: UNCHANGED vs pre-R1 baseline
- Independent audit: still pending R2 (AGY against exact R1)
