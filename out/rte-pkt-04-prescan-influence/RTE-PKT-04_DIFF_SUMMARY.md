# RTE-PKT-04 Diff Summary

## In-Scope Code Changes

`services/repo-truth-extractor/lib/intelligence_router.py`

- Added prescan influence common metadata helpers.
- Added available influence class inventory.
- Added path-normalized hint lookup so absolute runtime inventory paths can match prescan relative paths from source identity.
- Added narrow hint-source helpers for scope reduction, compression, routing/model hints, and tier override provenance.

`services/repo-truth-extractor/run_extraction_v5.py`

- Added prescan influence label helpers.
- Added scope-reduction, partition reorder, tier override, context brief, compression hint, routing/model hint, and phase hint labels at the runtime consumption points.
- Added top-level `PARTITIONS.json.prescan_influence` and per-partition `prescan_influence`.
- Added request metadata propagation for partition/context influence labels.
- Changed stage receipts so `scope_reduction_applied` remains false until an actual partitioning consumer applies scope reduction.
- Added `scope_reduction_enabled_by_prescan_allow_scope_reduction` for receipt-level operator visibility.
- Wired `--prescan-dir` into `RunnerConfig`, validated it through the imported prescan identity guard, and wrote `prescan_dir_receipt.json`.

`services/repo-truth-extractor/tests/test_prescan_influence_labels.py`

- Added local-only tests for accepted local/imported influence labels.
- Added rejected stale guard coverage.
- Added explicit scope-reduction flag coverage.
- Added compression hint proof-label redaction coverage.
- Added no-provider-call safety coverage.

## Forbidden Surface Check

No prompt files, promptset YAML, model-map YAML, structured-output contracts, provider clients, provider route configuration, pricing, compose/deployment files, or docs outside packet proof output were changed.
