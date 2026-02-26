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
1. For each SQLite table discovered in M1, execute `SELECT count(*) FROM <table>` and record the row count. Record: database path, table name, and row_count with evidence citing the query result.
2. Identify tables with zero rows and flag with `status: empty_table`. Identify tables with unusually large row counts (> 100,000) and flag with `status: large_table`.
3. Cross-reference table counts against expected operational ranges if documented in upstream artifacts.
4. Never extract row contents; only counts are permitted.
5. Legacy Context is intent guidance only and is never evidence.
6. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
7. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
8. Attach evidence to every non-derived field and every relationship edge.
9. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
10. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
11. Emit exactly the declared outputs and no additional files.

## Evidence Rules
- Every load-bearing value must carry at least one evidence object:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- `path` must be repo-relative (never absolute in norm artifacts).
- `excerpt` must be exact (no paraphrase) and <= 200 chars.
- If the source is ambiguous, include multiple evidence objects and set value to `UNKNOWN`.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent endpoints, handlers, dependencies, env vars, commands, or policy claims.
- Do not infer intent from filenames alone; require direct textual/code evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Table count query fails (e.g., table has been dropped since schema export): emit with `row_count: UNKNOWN` and `status: query_failed` with error message as evidence.
- Database is write-locked by another process: emit with `status: locked` and evidence; do not retry.

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
