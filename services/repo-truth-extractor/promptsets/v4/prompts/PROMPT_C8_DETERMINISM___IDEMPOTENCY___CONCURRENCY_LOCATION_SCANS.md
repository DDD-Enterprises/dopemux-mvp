# PROMPT_C8

## Goal
Produce `C8` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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
- `DOPE_MEMORY_CODE_SURFACE.json`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `TRINITY_ENFORCEMENT_SURFACE.json`
- `REFUSAL_AND_GUARDRAILS_SURFACE.json`
- `TASKX_INTEGRATION_SURFACE.json`
- `WORKFLOW_RUNNER_SURFACE.json`
- `API_DASHBOARD_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DETERMINISM_RISK_LOCATIONS.json`
- `IDEMPOTENCY_RISK_LOCATIONS.json`
- `CONCURRENCY_RISK_LOCATIONS.json`
- `SECRETS_RISK_LOCATIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DETERMINISM_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `DETERMINISM_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `IDEMPOTENCY_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `IDEMPOTENCY_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `CONCURRENCY_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `CONCURRENCY_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `SECRETS_RISK_LOCATIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C8`
    - `id_rule`: `SECRETS_RISK_LOCATIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the determinism, idempotency, and concurrency partition as primary scan surface.
2. Scan for non-deterministic functions: search for usage of `random.*`, `datetime.now()`, `time.time()`, and `uuid.uuid4()` in critical business logic paths.
3. Identify concurrency risks: search for `global` keyword, shared mutable state, and usage of `threading.Thread` or `asyncio.gather` without visible locking mechanisms.
4. Locate idempotency risks: identify database write operations (cross-reference with C3) that lack unique constraints, upsert logic, or idempotency keys.
5. Scan for secrets patterns: search for hardcoded strings matching regex patterns for API keys, tokens, or `SECRETS = "..."` assignments in non-config files.
6. Build risk registry: map each identified risk to its specific file location and classify severity based on the surrounding code context.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in risk assessment logic.
8. For each DETERMINISM_SURFACES item, populate `id`, required fields, and `evidence`.
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
Goal: DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json, SECRETS_RISK_LOCATIONS.json

Prompt:
- Scan for:
  - Non-deterministic functions (random, time, uuid) in critical paths.
  - Concurrency risks (global state mutation, race conditions).
  - Idempotency risks (DB writes without keys, retries with side effects).
  - Secrets patterns (APi keys, tokens).
```
