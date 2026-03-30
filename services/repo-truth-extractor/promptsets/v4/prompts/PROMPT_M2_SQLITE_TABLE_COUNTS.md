# PROMPT_M2

## Goal
Produce `M2` outputs for phase `M` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/**`
- `docker/**`
- `extraction/**`
- Upstream normalized artifacts available to this step:
- `M0_RUNTIME_EXPORT_INVENTORY.json`
- `M1_SQLITE_SCHEMA_SNAPSHOTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `M2_SQLITE_TABLE_COUNTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `M2_SQLITE_TABLE_COUNTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `M2`
    - `id_rule`: `M2_SQLITE_TABLE_COUNTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load runtime state and configuration as input for SQLite table counts
2. Extract SQLite table counts data: query live state, sanitize sensitive values, and capture metadata
3. Build SQLITE_TABLE_COUNTS: compile extracted data with timestamps and provenance
4. Validate export safety: ensure no secrets or sensitive data in output; redact if found
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
Goal: M2_SQLITE_TABLE_COUNTS.json

Prompt:
- Task: for each sqlite table discovered in M1, export count(*) only.
- Include:
  - db path
  - table name
  - row_count
  - status/error when count cannot be computed
- Hard rules:
  - No row-level exports.
  - No text/blob fields.
  - Keep output bounded and deterministic.
```
