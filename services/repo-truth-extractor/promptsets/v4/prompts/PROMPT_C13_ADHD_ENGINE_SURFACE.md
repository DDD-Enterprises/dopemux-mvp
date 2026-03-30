# PROMPT_C13

## Goal
Produce `C13` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract the ADHD engine subsystem: focus timer mechanics, dopamine reward loop patterns, task switching logic, cognitive load estimation, and accommodation surfaces.

## Inputs
- Source scope (scan these roots first):
  - `src/dopemux/adhd/**`
  - `services/adhd_engine/**`
  - `src/dopemux/cognitive/**`
  - `src/dopemux/focus/**`
  - `src/dopemux/hooks/**`
  - `src/dopemux/agent_orchestrator.py`
  - `services/agents/**`
  - `src/**`
  - `services/**`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `AGENT_ORCHESTRATION_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `ADHD_ENGINE_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `ADHD_ENGINE_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C13`
    - `id_rule`: `ADHD_ENGINE_SURFACE:<stable-hash(path|component|symbol)>`
    - `required_item_fields`: `id, component, subsystem, symbol, description, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
- `subsystem` enum: `focus_timer | dopamine_reward | task_switching | cognitive_load | accommodation | session_management | other`
- For `focus_timer` items, include: `timer_duration`, `break_logic`, `session_tracking`
- For `dopamine_reward` items, include: `reward_trigger`, `reward_mechanism`, `feedback_loop`
- For `cognitive_load` items, include: `load_metric`, `threshold`, `estimation_method`

## Extraction Procedure
1. Load upstream inventory and partitions; use the ADHD engine partition as primary scan surface
2. Scan `src/dopemux/adhd/**` and `services/adhd_engine/**` for ADHD accommodation implementations
3. Extract focus timer mechanics: Pomodoro-style timers, session duration configs, break logic
4. Extract dopamine reward loop patterns: completion rewards, streak tracking, progress visualization triggers
5. Extract task switching logic: context preservation, task queue management, interruption handling
6. Extract cognitive load estimation: complexity scoring, energy estimation, load-aware routing
7. Scan for accommodation surfaces: how the ADHD engine modifies behavior of other subsystems (task orchestrator, agents)
8. Cross-reference with `AGENT_ORCHESTRATION_SURFACE.json` to identify ADHD-agent integration points
9. Cross-reference with `EVENTBUS_SURFACE.json` for ADHD-related events (focus_start, focus_end, break_taken, etc.)
10. Build deterministic IDs using stable content keys (path/component/symbol)
11. Attach evidence to every non-derived field and every relationship edge
12. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash)
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps
14. Emit exactly the declared outputs and no additional files

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
