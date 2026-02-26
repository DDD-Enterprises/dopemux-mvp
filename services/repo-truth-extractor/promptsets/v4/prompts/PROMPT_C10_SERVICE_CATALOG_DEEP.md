# PROMPT_C10

## Goal
Produce `C10` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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
- `DOPE_MEMORY_CODE_SURFACE.json`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `TRINITY_ENFORCEMENT_SURFACE.json`
- `REFUSAL_AND_GUARDRAILS_SURFACE.json`
- `TASKX_INTEGRATION_SURFACE.json`
- `WORKFLOW_RUNNER_SURFACE.json`
- `API_DASHBOARD_SURFACE.json`
- `DETERMINISM_RISK_LOCATIONS.json`
- `IDEMPOTENCY_RISK_LOCATIONS.json`
- `CONCURRENCY_RISK_LOCATIONS.json`
- `SECRETS_RISK_LOCATIONS.json`
- `CODE_SURFACES_QA.json`
- `SERVICE_CATALOG.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `SERVICE_CATALOG.partX.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `SERVICE_CATALOG.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_service_id`
    - `canonical_writer_step_id`: `C10`
    - `id_rule`: `SERVICE_CATALOG:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, service_id, category, description, ports, health, repo_locations, entrypoints, interfaces, dependencies, config, evidence`
    - `required_registry_fields`: `service_id, category, description, ports, health, repo_locations, entrypoints, interfaces, dependencies, config`

## Extraction Procedure
1. Load `services/registry.yaml` as the canonical service list. For each registered service, create a catalog skeleton keyed by `service_id` and record the registry entry (port, transport, health_endpoint, category) with evidence citing `registry.yaml` line range.
2. Walk `services/**/main.py`, `services/**/app.py`, and `services/**/server.*` to locate the primary entrypoint for each service. Extract the framework (FastAPI, Flask, Express, etc.), the `app` or `server` object construction, and any lifespan/startup handlers. Record each entrypoint with file path and line range evidence.
3. For each service entrypoint, extract all route/endpoint declarations (HTTP methods, paths, handler function names) and MCP tool registrations. Cross-reference against upstream `SERVICE_ENTRYPOINTS.json` to validate completeness and detect unregistered endpoints.
4. Extract service dependencies by scanning import statements, client instantiations (HTTP clients, database connections, Redis connections, MCP client calls), and compose service `depends_on` declarations. Build a dependency list per service with evidence from both code and compose files.
5. Extract configuration surfaces: environment variables read (via `os.getenv`, `os.environ`, config loaders), config file paths loaded, default values, and required-vs-optional classification. Cross-reference against upstream `SECRETS_RISK_LOCATIONS.json` to flag sensitive config items.
6. Extract health check details: health endpoint path, response schema, readiness vs liveness distinction, and any dependency checks performed within the health handler (database ping, upstream service check).
7. Cross-reference discovered services against upstream artifacts (`EVENTBUS_SURFACE.json`, `DOPE_MEMORY_CODE_SURFACE.json`, `TRINITY_ENFORCEMENT_SURFACE.json`, `TASKX_INTEGRATION_SURFACE.json`) to enrich each catalog entry with event subscriptions, memory access patterns, enforcement hooks, and TaskX integrations.
8. Legacy Context is intent guidance only and is never evidence.
9. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
10. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.

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
- Service registered in `registry.yaml` but no matching code directory found under `services/`: emit catalog entry with all code-derived fields set to `UNKNOWN` and `missing_evidence_reason: no_code_directory`.
- Service code directory exists but is not registered in `registry.yaml`: include in catalog with `registry_status: unregistered` and evidence citing the directory path.
- Conflicting port assignments between `registry.yaml` and compose service definitions: emit both values with `status: needs_review` and evidence from each source.
