# `promptsets/v4/scripts/`

One-shot migration scripts for the v4 promptset's `model_map.yaml`.

## `migrate_model_map_v2_to_v3.py`

Migrates `model_map.yaml` from v2 (per-step routes only) to v3
(top-level `lane_defaults` + `tag_definitions` + per-step
`impact_class` + `capability_tier` + optional `tags`).

### Architecture (Option B — materialize routes)

- `lane_defaults` is the **canonical source** of routing intent.
- Per-step `*_routes` blocks are **kept** in v3 yaml, but for the 130
  non-override steps the routes are **materialized expansions** of the
  matching `lane_defaults` cell (using `value-default` cost profile).
- For the 6 override steps (`Z0`, `C10`, `S12`, `T0`, `T1`, `T3`) the
  per-step routes are **hand-curated in the script** and preserved
  byte-equal across re-runs.

This preserves the v2-shape per-step routes that every off-allowlist
reader (`phase_contract_map.py`, `run_extraction_v5.py`, `audit_tp008.py`,
`validate_pre_live_gate_v25.py`, `lib/promptgen/*`, `benchmarking/*`)
already consumes, while introducing `lane_defaults` as the canonical
source operators edit + re-migrate from.

### Operator workflow

```bash
# Initial migration: v2 yaml is backed up, v3 yaml replaces it in place.
cp promptsets/v4/model_map.yaml promptsets/v4/model_map.v2.yaml.bak
python promptsets/v4/scripts/migrate_model_map_v2_to_v3.py \
    --input promptsets/v4/model_map.v2.yaml.bak \
    --output promptsets/v4/model_map.yaml

# Subsequent re-run (idempotent): byte-equal output unless the migration
# script's hardcoded data tables change.
python promptsets/v4/scripts/migrate_model_map_v2_to_v3.py \
    --input promptsets/v4/model_map.yaml \
    --output promptsets/v4/model_map.yaml

# Dry-run + diff: see what would change without writing.
python promptsets/v4/scripts/migrate_model_map_v2_to_v3.py --dry-run --diff
```

### Editing routes

- **To change routing for a non-override step**: edit the
  `lane_defaults[cost_profile][lane_class][capability_tier]` cell in
  the migration script's `_VALUE_DEFAULT` / `_build_economy_cells()` /
  etc. structures, then re-run the migration. Per-step routes are
  re-materialized for all non-override steps.
- **To change routing for an override step**: edit the corresponding
  entry in `OVERRIDE_ROUTES`, then re-run the migration.
- **DO NOT** hand-edit `primary_routes` / `repair_routes` /
  `sidefill_routes` directly in `model_map.yaml` — the next migration
  run will overwrite the edit. The migration script is the only
  supported route-editing surface.

### Reference inputs

- `claudedocs/research/routing-design-2026-05.md` — Phase C cell map
  (10 populated cells × 4 cost profiles).
- `claudedocs/research/routing-consensus-2026-05.md` — Phase D
  reclassifications + 8-tag bounded enum + tag definitions.
- `claudedocs/research/step-complexity-analysis-2026-05.md` — Phase B.5
  per-step `reasoning_depth` + `partition_input_size_class` table.

### Audit gates (migration-time, fail-closed)

The migration raises `RuntimeError` if any of these invariants is
violated:

- Step count drops between input and output (silent step-drop guard).
- Two steps share a `step_id` in the input.
- A step lands in a `lane_defaults` cell that is not populated.
- `impact_class ∈ {structural, security_sensitive}` and
  `capability_tier != "critical"`.
- A step declares a `tag` not in the 8-tag enum.
- A step has `tags` but no `tag_rationale`.

These invariants are re-checked at runtime by the audit helpers in
`rte_promptset.py` (`validate_model_map_version`,
`audit_model_map_v3`) — defense in depth.
