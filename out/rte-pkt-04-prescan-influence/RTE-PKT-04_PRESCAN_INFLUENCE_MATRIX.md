# RTE-PKT-04 Prescan Influence Matrix

| Influence class | Runtime producer | Runtime consumer | Proof-visible surface | Applied behavior |
| --- | --- | --- | --- | --- |
| scope_reduction | `IntelligenceRouter.should_skip()` from `extraction_hints.skip_duplicates` and `grok_passes.optimize.skip_list` | `build_partitions()` | `PARTITIONS.json.prescan_influence.labels[]`; `prescan_stage_receipt.json` exposes enabled/not-applied stage state | Applied only when `--prescan-allow-scope-reduction` is true. Disabled candidates are labeled `applied=false`. |
| partition_reorder | `get_routing_priority()` and `reorder_partition()` | `build_partitions()` and `_apply_router_partition_hints()` | `PARTITIONS.json.prescan_influence`; per-partition `prescan_influence` | Applied when accepted router priority changes inventory or partition order. |
| tier_override | `get_model_tier()` with source helpers | `_apply_router_partition_hints()` and step route resolution | Per-partition `prescan_influence`; request `request_meta.prescan_influence` | Applied as a tier override label with old/new tier fields. |
| context_brief | `PartitionBriefGenerator` over router `code_report` | `_apply_router_partition_hints()` | Per-partition `prescan_influence`; request `request_meta.prescan_influence` | Applied as an advisory context brief label. Label does not include brief text. |
| compression_hint | `get_compression_hint()` | `build_partition_context()` | `context_stats.prescan_influence`; request `request_meta.prescan_influence` | Applied by replacing file content with existing compression hint text in prompt context. Proof label omits hint text. |
| routing_model_hint | `grok_passes.optimize.model_routing_hints` | `_apply_router_partition_hints()` via `get_model_tier()` | Per-partition `prescan_influence`; request `request_meta.prescan_influence` | Applied only as prescan-derived tier influence. Label sets `does_not_claim_executed_route=true`. |
| phase_hint | `grok_passes.optimize.phase_routing_overrides` | No v5 phase execution consumer observed | Per-partition `prescan_influence`; top-level `not_applied_influence_classes` | Explicitly labeled `applied=false` and `runtime_consumer=not_consumed_by_v5_partition_execution`. |

## Accepted State Boundary

Accepted local and imported routers expose common fields:

- `prescan_mode`
- `prescan_import_dir_if_any`
- `prescan_verdict`
- `can_influence_execution`
- `advisory_only`
- `influence_applied`
- `influence_classes`
- `available_influence_classes`
- `reason_codes`
- `generated_at`

## Rejected State Boundary

Rejected, stale, missing, malformed, unavailable, and skipped prescan states do not return an executable router from the validated import path. `_apply_router_partition_hints()` and `build_partition_context()` also check `can_influence_execution()` before applying router effects.

## Runtime Visibility Changes

- `prescan_stage_receipt.json` now distinguishes `scope_reduction_enabled_by_prescan_allow_scope_reduction` from actual `scope_reduction_applied`.
- `--prescan-dir` is wired into `RunnerConfig`, validated with the same identity gate as imported prescan, and writes `prescan_dir_receipt.json` under the run prescan artifact directory.
- `PARTITIONS.json` includes a top-level `prescan_influence` summary and per-partition labels when partition-level influence was applied or explicitly not applied.
- Request metadata receives merged partition/context influence labels when partition execution builds a request.
