# PROMPT_C4

## Goal
Produce `C4` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TRINITY_ENFORCEMENT_SURFACE.json`
- `REFUSAL_AND_GUARDRAILS_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TRINITY_ENFORCEMENT_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `TRINITY_ENFORCEMENT_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REFUSAL_AND_GUARDRAILS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `REFUSAL_AND_GUARDRAILS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the trinity boundary enforcement partition as primary scan surface.
2. Identify boundary enforcement points: search for decorators like `@boundary_check`, `@gatekeeper`, or `@authorize` that wrap sensitive functions.
3. Locate refusal logic and guardrails: search for keywords like "refusal", "forbidden", "unauthorized", "block", or "rail" in error handling, middleware, and validation modules.
4. Trace gating chains: identify sequences of checks in FastAPI/Flask middleware, base class methods, or decorator stacks.
5. Scan CLI paths and routers for explicit permission or boundary validation calls (e.g., `check_access(user, resource)`).
6. Build relationship graph: map which boundaries and guardrails protect which service entrypoints and data access paths.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in security policy enforcement.
8. For each TRINITY_SURFACES item, populate `id`, required fields, and `evidence`.
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
Goals: TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json

Prompt:
- Extract:
  - boundary checks, refusal artifacts, gating chains
  - where it's invoked (middleware, validators, routers, CLI paths)
```
