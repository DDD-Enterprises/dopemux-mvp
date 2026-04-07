# PROMPT_X9

## Goal
Produce `X9` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
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
- `FEATURE_INDEX_INVENTORY.json`
- `FEATURE_INDEX_PARTITIONS.json`
- `FEATURE_SURFACE.json`
- `FEATURE_CODE_MAP.json`
- `FEATURE_DOC_MAP.json`
- `FEATURE_DEP_GRAPH.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_INDEX_MERGED.json`
- `FEATURE_INDEX_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_INDEX_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X9`
    - `id_rule`: `FEATURE_INDEX_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FEATURE_INDEX_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X9`
    - `id_rule`: `FEATURE_INDEX_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all X-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all FEATURE_* artifacts into FEATURE_INDEX_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all X-Phase artifacts present, coverage complete, sort order deterministic; emit FEATURE_INDEX_QA
4. Cross-check coverage: verify every inventory item has corresponding extraction entries
5. For each output item, populate `id`, required fields, and `evidence` per schema contracts
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
# PROMPT_X9_MERGE___QA

TASK: Merge Feature Index outputs and emit QA.

INPUTS:
- Raw/partition outputs from X0..X4.

OUTPUTS:
- FEATURE_INDEX_MERGED.json
- FEATURE_INDEX_QA.json

RULES:
- Deterministic merge only; no rescans.
- Deduplicate by stable feature identity keys.
- Report coverage, unresolved mappings, and schema/required-field checks.
```
