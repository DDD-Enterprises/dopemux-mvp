# PROMPT_C17

## Goal
Produce `C17` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract all cognitive accommodation features across the codebase: ADHD accommodations, energy-aware routing, attention management, focus optimization, dopamine reward loops, and self-learning/adaptation mechanisms.

## Inputs
- Source scope (scan these roots first):
  - `src/dopemux/**`
  - `services/**`
  - `src/dopemux/adhd/**`
  - `services/adhd_engine/**`
  - `src/dopemux/cognitive/**`
  - `src/dopemux/focus/**`
  - `src/dopemux/energy/**`
  - `src/dopemux/attention/**`
  - `src/dopemux/learning/**`
  - `src/dopemux/agent_orchestrator.py`
  - `src/dopemux/routing/**`
  - `src/dopemux/routing_config.py`
  - `src/dopemux/hooks/**`
  - `config/**`
  - `configs/**`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `ADHD_ENGINE_SURFACE.json`
  - `AGENT_ORCHESTRATION_SURFACE.json`
  - `EVENTBUS_SURFACE.json`
  - `TASKX_INTEGRATION_SURFACE.json`
  - `SERVICE_CATALOG.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `COGNITIVE_FEATURES_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `COGNITIVE_FEATURES_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C17`
    - `id_rule`: `COGNITIVE_FEATURES_SURFACE:<stable-hash(path|feature_domain|symbol)>`
    - `required_item_fields`: `id, feature_domain, feature_name, subsystem, symbol, description, implementation_status, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `feature_domain` enum:
  - `adhd_accommodation` — focus timers, Pomodoro, break scheduling, interruption shielding
  - `energy_awareness` — energy-level estimation, energy-tagged routing, fatigue detection, low-energy fallbacks
  - `attention_management` — cognitive load scoring, context switching cost, attention budgets, distraction guards
  - `dopamine_reward` — streak tracking, completion celebrations, progress visualization, gamification hooks
  - `self_learning` — user preference adaptation, pattern recognition, model selection learning, feedback loops, drift detection
  - `task_accommodation` — task decomposition heuristics, complexity-aware scheduling, priority rewriting
- `implementation_status` enum: `implemented | stub | planned | partial | deprecated`
- For `adhd_accommodation` items, include: `timer_config`, `break_policy`, `session_tracking_method`
- For `energy_awareness` items, include: `energy_source`, `routing_impact`, `fallback_behavior`
- For `attention_management` items, include: `load_metric`, `threshold_config`, `mitigation_action`
- For `dopamine_reward` items, include: `reward_trigger`, `reward_mechanism`, `feedback_channel`
- For `self_learning` items, include: `learning_signal`, `adaptation_target`, `persistence_mechanism`, `drift_detection_method`
- For `task_accommodation` items, include: `decomposition_strategy`, `complexity_scorer`, `scheduling_rule`

## Extraction Procedure
1. Load upstream inventory and partitions; use the full code partition as scan surface.
2. Scan for ADHD accommodation features: locate code implementing focus timers, Pomodoro sessions (e.g., 25-minute intervals), break logic, and interruption shielding decorators.
3. Scan for energy-aware routing: functions/classes that assess user energy level, route tasks based on energy, implement low-energy fallbacks, tag tasks with energy requirements
4. Scan for attention management: cognitive load estimation functions, context-switch cost calculations, attention budget allocators, distraction guards
5. Scan for dopamine reward loops: streak counters, completion rewards, progress bars/visualizations, gamification elements, achievement systems
6. Scan for self-learning mechanisms: user preference stores, adaptive model selection, feedback ingestion, pattern recognition, recommendation adjustment, drift detection between expected and actual behavior
7. Scan for task accommodation: automatic task decomposition, complexity scoring (0.0-1.0 scale per workspace config), energy-aware scheduling, priority rewriting rules
8. Cross-reference with `ADHD_ENGINE_SURFACE.json` to ensure complete coverage and identify features outside the core engine
9. Cross-reference with `AGENT_ORCHESTRATION_SURFACE.json` to find cognitive features embedded in agent routing
10. Cross-reference with `TASKX_INTEGRATION_SURFACE.json` to find task-level accommodations
11. For each feature, classify `feature_domain`, extract `implementation_status` (implemented|stub|planned).
12. Build deterministic IDs using stable content keys (path/feature_domain/symbol).
13. Attach evidence to every non-derived field and every relationship edge.
14. Normalize arrays by stable sort keys; deduplicate by ID.
15. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
16. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
