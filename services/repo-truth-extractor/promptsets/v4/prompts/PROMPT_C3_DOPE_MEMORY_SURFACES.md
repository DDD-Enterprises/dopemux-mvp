# PROMPT_C3

## Goal
Produce `C3` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Focus on service runtime truths, interfaces, dependencies, and code-level ownership.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




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

## Extraction Procedure
1. Load upstream inventory and partitions; use the dope memory storage partition as primary scan surface.
2. Identify storage backend configurations: search for Redis, SQLite, Postgres, or ChromaDB connection strings and initialization code in `config/` or `services/**`.
3. Locate schema definitions and migration files: scan `*.sql` files and Python migration scripts (e.g., Alembic `env.py` or `versions/*.py`) to map data structures.
4. Find all database write locations: search for raw `INSERT`, `UPDATE`, `DELETE` SQL statements or ORM equivalent calls like `.add(`, `.save(`, `.update(`.
5. Identify TTL and retention enforcement: search for `expire`, `ttl`, `cleanup_stale`, or `retention` keywords in storage-related modules.
6. Build relationship graph: map the connections between code symbols (functions/classes) and the specific database tables or collections they manipulate.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in storage settings across environments.
8. For each DOPE_MEMORY_SURFACES item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

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
