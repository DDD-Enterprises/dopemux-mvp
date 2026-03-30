# PROMPT_X0

## Goal
Produce `X0` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `components/**`
- `compose/**`
- `config/**`
- `configs/**`
- `contracts/**`
- `dashboard/**`
- `docker/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `plugins/**`
- `profiles/**`
- `review_artifacts/**`
- `scripts/**`
- `services/**`
- `shared/**`
- `src/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `tools/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `UPGRADES/**`
- `vendor/**`


- `extraction/**`
- `reports/**`

- `README.md`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_INDEX_INVENTORY.json`
- `FEATURE_INDEX_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_INDEX_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X0`
    - `id_rule`: `FEATURE_INDEX_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FEATURE_INDEX_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X0`
    - `id_rule`: `FEATURE_INDEX_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan feature-relevant sources (user-facing code, docs, configs) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the feature-relevant sources (user-facing code, docs, configs) domain
3. Build FEATURE_PARTITIONS by grouping files into logical categories with rationale
4. For each FEATURE_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each FEATURE_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_X0_FEATURE_INDEX_INVENTORY___PARTITION_PLAN

TASK: Build feature-index inventory and deterministic partition plan.

SCAN TARGETS:
- services/
- src/
- docs/
- config/
- scripts/
- Makefile
- docker-compose*.yml

OUTPUTS:
- FEATURE_INDEX_INVENTORY.json
- FEATURE_INDEX_PARTITIONS.json

RULES:
- Enumerate candidate feature surfaces, owning code paths, and related docs.
- Partition deterministically for downstream X1 extraction.
- Preserve literal evidence and source paths.
```
