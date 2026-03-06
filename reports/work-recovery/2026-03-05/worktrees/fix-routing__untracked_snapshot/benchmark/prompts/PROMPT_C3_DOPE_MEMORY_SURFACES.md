# PROMPT_C3

## Goal
Produce `C3` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Focus on service runtime truths, interfaces, dependencies, and code-level ownership.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docker/**`
- `compose.yml`
- `docker-compose*.yml`
- `services/registry.yaml`
- Upstream normalized artifacts available to this step:
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`
- `SERVICE_ENTRYPOINTS.json`
- `EVENTBUS_SURFACE.json`
- `EVENT_PRODUCERS.json`
- `EVENT_CONSUMERS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOPE_MEMORY_CODE_SURFACE.json`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOPE_MEMORY_CODE_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_CODE_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DOPE_MEMORY_SCHEMAS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_SCHEMAS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOPE_MEMORY_DB_WRITES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DOPE_MEMORY_DB_WRITES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream artifacts through `EVENT_CONSUMERS.json`; use the code inventory to scope discovery of dope-memory modules.
2. Scan source for all storage backend implementations: identify database connection factories, ORM model definitions, raw SQL execution sites, and key-value store adapters; classify each by `component` and `symbol`.
3. Extract schema sources: locate SQL migration files, Alembic/migration scripts, SQLAlchemy model definitions, Pydantic models used for DB serialization, and any inline CREATE TABLE/ALTER TABLE statements; record file:line evidence.
4. Identify all DB write locations: find every INSERT, UPDATE, DELETE, UPSERT, or equivalent ORM call (`.add()`, `.commit()`, `.save()`, `.delete()`); for each, record the table/collection, the calling function, and the owning service.
5. Locate TTL and retention enforcement points: search for expiry configurations, cleanup cron jobs, retention policy constants, and scheduled deletion tasks; map each to the affected storage backend.
6. For each output artifact item, populate required fields (`id`, `component`, `symbol`, `path`, `line_range`, `evidence`) using the appropriate id_rule.
7. Legacy Context is intent guidance only and is never evidence.
8. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
9. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
10. Attach evidence to every non-derived field and every relationship edge.
11. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
13. Emit exactly the declared outputs and no additional files.

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
- Schema-code drift: if a migration file defines a column that no ORM model references (or vice versa), emit both items and flag the drift in `coverage_notes` with evidence from both sources.
- Implicit write via ORM cascade: if a DB write is triggered by ORM cascade (e.g., `cascade='all,delete-orphan'`) rather than an explicit call, emit with `kind: cascade_write` and evidence of the cascade configuration.

## Legacy Context (for intent only; never as evidence)
```markdown
Goals: DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json

Prompt:
- Extract:
  - storage backends
  - schema sources (SQL, migrations)
  - all DB write locations (insert/update/delete) with context
  - TTL/retention enforcement points
```
