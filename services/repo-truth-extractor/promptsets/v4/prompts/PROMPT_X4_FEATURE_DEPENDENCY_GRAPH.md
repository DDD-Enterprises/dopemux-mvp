# PROMPT_X4

## Goal
Produce `X4` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_DEP_GRAPH.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_DEP_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X4`
    - `id_rule`: `FEATURE_DEP_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the feature dependency graph partition as primary scan surface
2. Extract feature dependency graph facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted feature dependency graph elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each FEATURE_DEPS item, populate `id`, required fields, and `evidence`
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
# PROMPT_X4_FEATURE_DEPENDENCY_GRAPH

TASK: Build feature dependency graph across services, configs, and workflows.

OUTPUTS:
- FEATURE_DEP_GRAPH.json

REQUIREMENTS:
- Emit directed dependencies between features and critical infra/services.
- Include runtime-mode and environment dependencies where observable.
- Preserve cycle information; do not collapse conflicting edges.
```
