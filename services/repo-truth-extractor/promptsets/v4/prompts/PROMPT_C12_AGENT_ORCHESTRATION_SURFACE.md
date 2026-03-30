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
1. Load upstream inventory and partitions; use the agent orchestration partition as primary scan surface.
2. Locate the `AgentType` enum (or equivalent type union) — extract every enum value with its string representation and evidence.
3. Locate the `AgentManager` class (or equivalent orchestrator) — extract all public methods with signatures, parameters, and return types.
4. Scan for agent launch patterns: factory methods (e.g., `AgentFactory.get_agent`), `spawn()`, `create_agent()`, `run_in_background=True`, subprocess invocations, or MCP tool registrations that instantiate agents.
5. Scan for inter-agent communication protocols: search for eventbus subscriptions, direct method calls between agent instances, and usage of `AgentMessage` or equivalent payload types.
6. Extract lifecycle state machines: trace transitions through `READY`, `BUSY`, `IDLE`, `DONE`, and `ERROR` states in agent logic.
7. Cross-reference with `EVENTBUS_SURFACE.json` to identify agent-eventbus bindings and specific message topics.
8. Build deterministic IDs using stable content keys (path/agent_type/symbol).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID.
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
