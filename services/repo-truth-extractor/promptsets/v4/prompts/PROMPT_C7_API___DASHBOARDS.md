# PROMPT_C7

## Goal
Produce `C7` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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

- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`

- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`

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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `API_DASHBOARD_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `API_DASHBOARD_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C7`
    - `id_rule`: `API_DASHBOARD_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, http_method, path_template, handler_symbol, auth_required, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "API_DASHBOARD_SURFACE:<hash>",
  "http_method": "GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|WEBSOCKET",
  "path_template": "<route path, e.g. '/api/v1/tasks/{task_id}'>",
  "handler_symbol": "<function or method name handling the route>",
  "service_name": "<service name from registry.yaml>",
  "request_body_schema": "<Pydantic model name or null for no body>",
  "response_model": "<Pydantic model name or null if untyped>",
  "response_codes": ["200", "404", "422"],
  "auth_required": true,
  "auth_mechanism": "depends_injection|bearer_token|api_key|none|unknown",
  "rate_limited": false,
  "rate_limit_spec": "<e.g. '100/minute' or null>",
  "tags": ["<FastAPI tags if declared>"],
  "is_deprecated": false,
  "path": "<repo-relative path to route definition>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### HTTP Method Definitions
- **GET**: Read-only retrieval of resources
- **POST**: Create new resources or trigger actions
- **PUT**: Full replacement of a resource
- **PATCH**: Partial update of a resource
- **DELETE**: Remove a resource
- **OPTIONS**: CORS preflight or capability discovery
- **HEAD**: Headers-only GET (no body)
- **WEBSOCKET**: WebSocket upgrade endpoint

### Auth Mechanism Definitions
- **depends_injection**: Auth enforced via FastAPI `Depends()` (e.g., `Depends(get_current_user)`)
- **bearer_token**: JWT or OAuth2 Bearer token in Authorization header
- **api_key**: API key in header, query parameter, or cookie
- **none**: No authentication required (public endpoint)
- **unknown**: Auth presence unclear from code evidence

### Severity Classification (for dashboard items)
- **critical**: Endpoint has no auth but handles sensitive data
- **high**: Endpoint missing error handling or has unvalidated inputs
- **medium**: Endpoint lacks rate limiting or response schema
- **low**: Documentation or deprecation annotation missing

### Worked Example
```json
{
  "id": "API_DASHBOARD_SURFACE:b7e2d1f8",
  "http_method": "POST",
  "path_template": "/api/v1/tasks/{task_id}/decompose",
  "handler_symbol": "decompose_task",
  "service_name": "task-orchestrator",
  "request_body_schema": "DecomposeRequest",
  "response_model": "DecomposeResponse",
  "response_codes": ["200", "404", "422"],
  "auth_required": false,
  "auth_mechanism": "none",
  "rate_limited": false,
  "rate_limit_spec": null,
  "tags": ["tasks"],
  "is_deprecated": false,
  "path": "services/task-orchestrator/app/api/pm_tools.py",
  "line_range": [45, 78],
  "status": "ok",
  "evidence": [{"path": "services/task-orchestrator/app/api/pm_tools.py", "line_range": [45, 47], "excerpt": "@router.post('/api/v1/tasks/{task_id}/decompose', response_model=DecomposeResponse)"}]
}
```

## Extraction Procedure
1. Load upstream inventory and partitions; use the API endpoint and dashboard partition as primary scan surface.
2. Extract API routes: scan `src/**` and `services/**` for router definitions (e.g., `APIRouter()`, `Blueprint()`) and route decorators (e.g., `@app.get`, `@router.post`).
3. Identify dashboard definitions: search for UI components in `dashboard/**`, `ui-dashboard/**`, or `components/**` that render system state or metrics.
4. Locate monitoring and health endpoints: search for routes like `/health`, `/metrics`, `/status`, or Prometheus-style exporter configurations.
5. Identify frontend-to-backend mappings: search for `fetch(`, `axios.`, or `api.get(` calls in JavaScript/TypeScript files to identify backend dependencies.
6. Build relationship graph: trace connections between API endpoints and the dashboard components that display their data.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in API surface definitions.
8. For each API_DASHBOARD_SURFACES item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

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
- Hidden dependency: if an element depends on something not explicitly documented, emit with `status: implicit_dependency`
- Shadowed config: if a config overrides another at a different level, emit both with `status: shadow`

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: API_DASHBOARD_SURFACE.json

Prompt:
- Extract API routes, dashboard definitions, and monitoring endpoints.
- Cite file and line ranges.
```
