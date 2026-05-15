# RTE-PKT-04 Rejected Influence Guards

## Guarded States

The following states are non-authoritative and cannot apply prescan influence:

- `imported_prescan_rejected_stale`
- `imported_prescan_missing_metadata`
- malformed or missing imported artifact
- `skip_prescan`
- `local_prescan_failed`
- `local_prescan_unavailable`
- missing or rejected `--prescan-dir`

## Observed Guard Paths

- `IntelligenceRouter.load_imported()` returns `(None, validation)` when identity validation fails.
- `run_integrated_prescan_stage()` writes a rejected receipt and returns no router for rejected imports.
- `build_partitions()` only applies skip/scope and priority behavior when `_router_can_influence_execution(router)` is true.
- `_apply_router_partition_hints()` returns without mutation when the router is absent or cannot influence execution.
- `build_partition_context()` only applies compression hints when the router can influence execution.
- `--prescan-dir` now uses `_load_imported_prescan_router()` and writes `prescan_dir_receipt.json`; a failed validation does not update `cfg.router` or `_ACTIVE_INTELLIGENCE_ROUTER`.

## Targeted Test Evidence

`test_rejected_stale_prescan_cannot_apply_influence` writes a stale imported prescan fixture with a mismatched corpus manifest hash. `IntelligenceRouter.load_imported()` returns no router, `build_partitions()` receives no executable router, and the skip candidate remains in the partition.

`test_scope_reduction_requires_explicit_allow_flag` proves accepted skip candidates remain present when scope reduction is disabled and are removed only when the explicit allow flag is true.
