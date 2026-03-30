# PROMPT_A13

## Goal
Produce `A13` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Extract hook contracts and event flow graphs: map every hook trigger to its handler, event types, transport mechanism, and lifecycle phase to produce a complete event envelope model.

## Inputs
- Source scope (scan these roots first):
  - `src/dopemux/hooks/**`
  - `src/dopemux/mcp/hooks.py`
  - `src/dopemux/events/**`
  - `src/dopemux/event_bus.py`
  - `.claude/hooks/**`
  - `.githooks/**`
  - `.vibe/**`
  - `.claude/**`
  - `.dopemux/**`
  - `.github/**`
  - `.taskx/**`
  - `mcp-proxy-config.copilot.yaml`
  - `compose/**`
  - `config/**`
  - `configs/**`
  - `docker/**`
  - `installers/**`
  - `ops/**`
  - `scripts/**`
  - `tools/**`
- Upstream normalized artifacts available to this step:
  - `REPOCTRL_INVENTORY.json`
  - `REPOCTRL_PARTITIONS.json`
  - `REPO_HOOKS_SURFACE.json`
  - `REPO_MCP_SERVER_DEFS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `HOOK_CONTRACT_SURFACE.json`
- `EVENT_FLOW_GRAPH.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `HOOK_CONTRACT_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A13`
    - `id_rule`: `HOOK_CONTRACT_SURFACE:<stable-hash(path|trigger_source|handler_path)>`
    - `required_item_fields`: `id, trigger_source, handler_path, event_types, transport_mechanism, lifecycle_phase, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `EVENT_FLOW_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A13`
    - `id_rule`: `EVENT_FLOW_GRAPH:<stable-hash(source|target|event_type)>`
    - `required_item_fields`: `id, source, target, event_type, transport, direction, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
- `lifecycle_phase` enum: `pre_launch | post_launch | on_message | on_complete | on_error`
- `transport_mechanism` enum: `eventbus | direct_call | webhook | mcp_tool | file_watch | signal | other`
- `direction` enum: `producer_to_consumer | request_response | broadcast | pub_sub`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json`, `REPOCTRL_PARTITIONS.json`, and `REPO_HOOKS_SURFACE.json`.
2. Scan `src/dopemux/hooks/**/*.py` and `src/dopemux/mcp/hooks.py` for registration and handler patterns:
   - Search for decorators: `@hook`, `@on_event`, `@register_handler`.
   - Search for registration calls: `event_bus.subscribe()`, `hooks.add()`, `callback_manager.register()`.
3. Map every hook trigger to its operational contract:
   - `trigger_source`: identify the event ID or condition that fires the hook.
   - `handler_path`: locate the function or script that executes on trigger.
   - `event_types`: identify the literal event names (e.g., `TASK_CREATED`, `GIT_PRE_COMMIT`).
   - `transport_mechanism`: categorize as `eventbus`, `direct_call`, `webhook`, `mcp_tool`, or `signal`.
   - `lifecycle_phase`: identify phase (e.g., `pre_launch`, `post_launch`, `on_message`, `on_error`).
4. Scan `src/dopemux/event_bus.py` and `src/dopemux/events/*.py` to build the `EVENT_FLOW_GRAPH`:
   - Identify `producers`: where `event_bus.publish()` or `emit()` is called.
   - Identify `consumers`: where handlers are registered via subscription.
   - Trace flow from `source` component to `target` component per `event_type`.
5. Build deterministic IDs using stable content keys (path|trigger_source|handler_path).
6. Attach evidence to every non-derived field, anchoring to both the trigger registration AND the handler definition.
7. Normalize arrays by stable sort keys; deduplicate by ID.
8. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
9. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
