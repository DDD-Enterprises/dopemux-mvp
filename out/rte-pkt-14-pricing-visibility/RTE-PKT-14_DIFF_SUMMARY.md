# RTE-PKT-14 Diff Summary

## OBSERVED

- Added `lib/pricing_surface.py` as the static pricing/economic-surface helper.
- Restored predecessor route metadata propagation by making `llm_runtime` request metadata use static route identity and by importing `classify_route_identity` in `run_extraction_v5.py`.
- Added pricing/economic fields to v5 request metadata, route fingerprint metadata, legacy spend tracker cost events, `SpendLedger` rows, pricing coverage rows, and direct-model spend estimates.
- Added `test_pricing_surface_static_identity.py` for direct xAI, OpenRouter x-ai, matrix coverage, spend row preservation, and no-provider-call safety.

## INFERRED

- Existing pricing rates were preserved. The change affects pricing authority labels and metadata shape, not catalog rates.
- Existing artifact shape is preserved by additive fields.

## UNKNOWN

- No live billing, retention, ZDR, rate-limit, schema acceptance, returned-model, or upstream OpenRouter x-ai behavior was validated.
- Dedicated worktree, branch, commit, push, and PR proof are unavailable because `.git` write operations were blocked by sandbox permissions.

## Files Changed

- `services/repo-truth-extractor/benchmarking/direct_model/spend.py`
- `services/repo-truth-extractor/benchmarking/pricing/coverage.py`
- `services/repo-truth-extractor/lib/pricing_surface.py`
- `services/repo-truth-extractor/lib/spend_ledger.py`
- `services/repo-truth-extractor/llm_runtime.py`
- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/tests/test_pricing_surface_static_identity.py`
