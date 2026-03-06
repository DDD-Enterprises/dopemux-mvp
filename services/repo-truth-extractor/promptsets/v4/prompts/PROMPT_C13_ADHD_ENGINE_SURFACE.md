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
- Do not invent ADHD mechanisms, timer configurations, reward patterns, or cognitive metrics.
- Do not infer ADHD functionality from variable names alone; require direct code evidence (function bodies, class definitions, config values).
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.
- Do not assume a module implements ADHD accommodation without verifying its actual behavior in code.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- No ADHD engine found: if `src/dopemux/adhd/` and `services/adhd_engine/` do not exist, emit empty container with `coverage_notes: "ADHD engine directories not found"`.
- Partial implementation: if ADHD features are partially implemented, emit with `status: partial_implementation` and evidence of what exists vs. stubs.
- Hidden coupling: if ADHD engine modifies other subsystems through side effects, emit with `status: implicit_coupling`.
