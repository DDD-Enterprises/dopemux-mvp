# PROMPT_C15

## Goal
Produce `C15` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract the service endpoint surface: HTTP routes, MCP tool definitions, eventbus topics, gRPC services, and WebSocket endpoints across all services.

## Inputs
- Source scope (scan these roots first):
  - `services/**`
  - `src/**`
  - `components/**`
  - `docker/**`
  - `compose.yml`
  - `docker-compose*.yml`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_CATALOG.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `REPO_MCP_SERVER_DEFS.json`
  - `EVENTBUS_SURFACE.json`
  - `API_DASHBOARD_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `SERVICE_ENDPOINT_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `SERVICE_ENDPOINT_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C15`
    - `id_rule`: `SERVICE_ENDPOINT_SURFACE:<stable-hash(path|service_id|endpoint)>`
    - `required_item_fields`: `id, service_id, endpoint_type, endpoint_path, method, handler_symbol, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `endpoint_type` enum: `http_route | mcp_tool | eventbus_topic | grpc_service | websocket | cli_endpoint | other`
- `method` values: `GET | POST | PUT | DELETE | PATCH | SUBSCRIBE | PUBLISH | CALL | STREAM | N/A`
- For `http_route` items, include: `url_pattern`, `request_schema`, `response_schema`, `auth_required`
- For `mcp_tool` items, include: `tool_name`, `input_schema`, `description`
- For `eventbus_topic` items, include: `topic_name`, `payload_schema`, `direction` (publish|subscribe)

## Extraction Procedure
1. Load upstream inventory and partitions; use the service endpoint partition as primary scan surface
2. Scan for HTTP route registrations: FastAPI `@app.get/post/put/delete`, Flask routes, Django URL patterns
3. Scan for MCP tool definitions: `@server.tool()` decorators, tool registration calls, MCP server manifests
4. Scan for eventbus topic subscriptions and publications: `subscribe()`, `publish()`, topic constant definitions
5. Scan for WebSocket endpoints: `@app.websocket()`, WebSocket handler registrations
6. For each endpoint, extract: service_id, endpoint path/name, HTTP method, handler function symbol
7. Cross-reference with `SERVICE_CATALOG.json` to associate endpoints with their owning service
8. Cross-reference with `REPO_MCP_SERVER_DEFS.json` to validate MCP tool definitions
9. Cross-reference with `EVENTBUS_SURFACE.json` to validate eventbus topic bindings
10. Build deterministic IDs using stable content keys (path/service_id/endpoint)
11. Attach evidence to every non-derived field and every relationship edge
12. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash)
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps
14. Emit exactly the declared outputs and no additional files

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
- Do not invent endpoints, routes, MCP tools, or eventbus topics.
- Do not infer endpoint behavior from URL patterns alone; require handler function evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Dynamic route registration: if routes are registered at runtime, emit with `status: dynamic_registration`.
- Undocumented endpoints: emit with `description: UNKNOWN` and handler evidence only.
