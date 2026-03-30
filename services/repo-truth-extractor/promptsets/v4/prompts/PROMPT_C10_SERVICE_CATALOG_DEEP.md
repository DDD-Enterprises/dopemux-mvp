# PROMPT_C10

## Goal
Produce `C10` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Focus on service runtime truths, interfaces, dependencies, and code-level ownership.

## Inputs
- Source scope (scan these roots first):
  - `src/**`
  - `services/**`
  - `services/agents/**`
  - `components/**`
  - `dashboard/**`
  - `plugins/**`
  - `ui-dashboard/**`
  - `ui-dashboard-backend/**`
  - `src/dopemux/agent_orchestrator.py`
  - `src/dopemux/hooks/**`
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
1. Load upstream inventory and partitions; use the deep service catalog partition as primary scan surface.
2. Aggregate service identity: extract names and IDs from `services/registry.yaml`, `package.json`, or `pyproject.toml` files within service directories.
3. Identify network exposure: scan `compose.yml`, `Dockerfile`, and code for `EXPOSE` instructions, port assignments, and bind addresses.
4. Locate health check logic: search for dedicated health check functions, `/health` routes, or `HEALTHCHECK` instructions in Dockerfiles.
5. Map repository locations: identify the primary source directories and owners for each service listed in the registry.
6. Synthesize deep facts: combine entrypoint data (from C1), interface data (from C2, C7), and dependency data (from C5, C16) into a unified service profile.
7. Identify configuration surfaces: search for `os.getenv`, `pydantic.BaseSettings`, or `.env` file loading that defines the service's runtime configuration.
8. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in service catalog metadata.
9. For each SERVICE_CATALOG_DEEP item, populate `id`, required fields, and `evidence`.
10. Legacy Context is intent guidance only and is never evidence.
11. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
12. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
13. Attach evidence to every non-derived field and every relationship edge.
14. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
15. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
16. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
