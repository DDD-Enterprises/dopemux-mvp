# PROMPT_C12

## Goal
Produce `C12` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract agent orchestration surfaces: the `AgentType` enum, `AgentManager` class patterns, agent launch/spawn mechanisms, inter-agent communication protocols, and lifecycle state machines.

## Inputs
- Source scope (scan these roots first):
  - `src/dopemux/agent_orchestrator.py`
  - `services/agents/**`
  - `src/dopemux/hooks/**`
  - `src/dopemux/agents/**`
  - `src/dopemux/mcp/**`
  - `src/**`
  - `services/**`
  - `components/**`
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
- `AGENT_ORCHESTRATION_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `AGENT_ORCHESTRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C12`
    - `id_rule`: `AGENT_ORCHESTRATION_SURFACE:<stable-hash(path|agent_type|symbol)>`
    - `required_item_fields`: `id, item_type, agent_type, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
- `item_type` enum: `agent_type_enum_value | manager_method | comm_protocol | lifecycle_state | launch_pattern | spawn_pattern`
- `agent_type` values: extracted directly from the `AgentType` enum definition with code evidence
- For `manager_method` items, include: `method_name`, `parameters`, `return_type`, `description`
- For `comm_protocol` items, include: `protocol_type`, `producer`, `consumer`, `payload_shape`
- For `lifecycle_state` items, include: `state_name`, `transitions_to`, `trigger`

## Extraction Procedure
1. Load upstream inventory and partitions; use the agent orchestration partition as primary scan surface
2. Locate the `AgentType` enum (or equivalent type union) — extract every enum value with its string representation and evidence (path + line_range + excerpt)
3. Locate the `AgentManager` class (or equivalent orchestrator) — extract all public methods with signatures, parameters, and return types
4. Scan for agent launch patterns: factory methods, `spawn()`, `create_agent()`, subprocess invocations, or MCP tool registrations that instantiate agents
5. Scan for inter-agent communication protocols: eventbus subscriptions, direct method calls between agent instances, MCP tool invocations, shared state patterns
6. Extract lifecycle state machines: initialization → running → paused → completed → error states with transition triggers
7. Cross-reference with `EVENTBUS_SURFACE.json` and `EVENT_PRODUCERS.json` / `EVENT_CONSUMERS.json` to identify agent-eventbus bindings
8. Build deterministic IDs using stable content keys (path/agent_type/symbol)
9. Attach evidence to every non-derived field and every relationship edge
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash)
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps
12. Emit exactly the declared outputs and no additional files

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
- `AgentType` enum values MUST have evidence pointing to the enum class definition, not usage sites.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent agent types, orchestration methods, communication protocols, or lifecycle states.
- Do not infer agent behavior from class names alone; require direct code evidence (enum definitions, method bodies, decorator registrations).
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.
- Do not assume an agent type exists because a directory is named after it; verify `AgentType` enum evidence.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- No `AgentType` enum found: emit items with `agent_type: UNKNOWN` and note the enum pattern was not located.
- Dynamic agent registration: if agents are registered at runtime (not statically), emit with `status: dynamic_registration` and capture the registration call evidence.
- Hidden agent communication: if agents communicate through shared state rather than explicit protocols, emit with `status: implicit_communication`.
