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
1. Load upstream inventory and partitions; use the full code partition as scan surface
2. Scan for ADHD accommodation features: focus timers, Pomodoro sessions, break logic, interruption shielding, session boundaries (25-minute focus windows per workspace config)
3. Scan for energy-aware routing: functions/classes that assess user energy level, route tasks based on energy, implement low-energy fallbacks, tag tasks with energy requirements
4. Scan for attention management: cognitive load estimation functions, context-switch cost calculations, attention budget allocators, distraction guards
5. Scan for dopamine reward loops: streak counters, completion rewards, progress bars/visualizations, gamification elements, achievement systems
6. Scan for self-learning mechanisms: user preference stores, adaptive model selection, feedback ingestion, pattern recognition, recommendation adjustment, drift detection between expected and actual behavior
7. Scan for task accommodation: automatic task decomposition, complexity scoring (0.0-1.0 scale per workspace config), energy-aware scheduling, priority rewriting rules
8. Cross-reference with `ADHD_ENGINE_SURFACE.json` to ensure complete coverage and identify features outside the core engine
9. Cross-reference with `AGENT_ORCHESTRATION_SURFACE.json` to find cognitive features embedded in agent routing
10. Cross-reference with `TASKX_INTEGRATION_SURFACE.json` to find task-level accommodations
11. For each feature, classify `feature_domain`, extract `implementation_status` based on code evidence (full implementation vs. stub/TODO)
12. Build deterministic IDs using stable content keys (path/feature_domain/symbol)
13. Attach evidence to every non-derived field and every relationship edge
14. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash)
15. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps
16. Emit exactly the declared outputs and no additional files

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
- `implementation_status` must cite evidence: `implemented` requires function body, `stub` requires TODO/placeholder, `planned` requires doc/comment reference.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent cognitive features, learning mechanisms, or energy-aware behaviors.
- Do not infer cognitive accommodation from variable names alone; require direct code evidence (function bodies, class definitions, config values).
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.
- Do not assume a feature is "self-learning" without evidence of feedback loops or adaptation logic.
- Do not classify a simple timer as an "ADHD accommodation" without evidence it serves that purpose.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Feature spread across multiple files: emit a single item with multiple evidence objects spanning all relevant source locations.
- Ambiguous feature domain: if a feature spans multiple domains (e.g., energy-aware ADHD accommodation), emit with the primary domain and add `related_domains: [...]`.
- Planned-but-not-implemented features: emit with `implementation_status: planned` and evidence from documentation/comments only.
- Self-learning without persistence: if adaptation logic exists but has no persistence mechanism, emit with `persistence_mechanism: UNKNOWN` and `status: volatile_only`.
