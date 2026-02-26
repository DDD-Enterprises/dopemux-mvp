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
1. Scan `src/**` and `services/**` for storage backend implementations: classes or modules that wrap database clients (PostgreSQL, SQLite, Redis, Qdrant, file-based stores). For each backend, record the client library used, connection initialization pattern, and the file path with line range evidence. Emit these as `DOPE_MEMORY_CODE_SURFACE.json` items.
2. Locate schema definition sources: SQL files (`*.sql`), migration scripts (Alembic, raw SQL migrations), ORM model definitions (SQLAlchemy, Pydantic models used for DB schemas), and JSON Schema files. For each schema source, record the table/collection name, column definitions (if explicit), and file path with line range.
3. Extract all database write locations by scanning for SQL `INSERT`, `UPDATE`, `DELETE` statements (both raw and ORM-based), Redis `SET`/`HSET`/`LPUSH` calls, and Qdrant upsert operations. For each write site, record the target table/collection, the operation type, the calling function, and file path with line range evidence. Emit these as `DOPE_MEMORY_DB_WRITES.json` items.
4. Identify TTL and retention enforcement points: scan for `EXPIRE`, `TTL`, `retention`, `cleanup`, `purge`, or `vacuum` patterns in code and configuration. Record the retention policy (duration, condition), the target data store, and evidence.
5. Extract connection pooling and lifecycle management: pool size configuration, connection reuse patterns, graceful shutdown hooks that close database connections. Record with evidence from code or compose environment variables.
6. Cross-reference discovered storage surfaces against upstream `SERVICE_ENTRYPOINTS.json` and `EVENTBUS_SURFACE.json` to identify which services own which storage backends and whether event-driven writes exist.
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
- Database write uses dynamically constructed table names or query strings: emit with `target_table: UNKNOWN` and `status: dynamic_query` with evidence citing the expression.
- Schema definition split across multiple migration files with no single canonical source: emit all migration files as evidence and set `schema_completeness: partial` with `missing_evidence_reason: distributed_migrations`.

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
