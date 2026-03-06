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
1. Load upstream inventory and partitions; use the hooks/events partition as primary scan surface
2. Scan `src/dopemux/hooks/**` for hook registration patterns: decorators, registration calls, handler mappings
3. Scan `src/dopemux/events/**` and `src/dopemux/event_bus.py` for event type definitions, publish/subscribe patterns
4. Scan `.claude/hooks/**` for Claude Code hook definitions (pre/post hooks, validation hooks)
5. Scan `.githooks/**` for git hook scripts and their trigger conditions
6. For each hook contract, extract the event envelope: `trigger_source` → `handler_path` → `event_types[]` → `transport_mechanism`
7. Classify each hook into a `lifecycle_phase` based on when it fires in the system lifecycle
8. Build the event flow graph: for each event type, trace producer → consumer paths with transport annotations
9. Cross-reference with `REPO_HOOKS_SURFACE.json` to ensure coverage of previously identified hooks
10. Build deterministic IDs using stable content keys (path/trigger_source/handler_path for contracts, source/target/event_type for flows)
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
- Hook contracts must include evidence for both the trigger registration AND the handler definition.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent hook contracts, event types, handlers, or transport mechanisms.
- Do not infer event flow from naming conventions alone; require direct code evidence (registration calls, decorators, import chains).
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.
- Do not assume a function is a hook handler without verifying its registration or decorator.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Orphaned hooks: hooks registered but handler not found — emit with `handler_path: UNKNOWN` and `status: orphaned`
- Circular event flows: if event A triggers B which triggers A, emit both edges and add `status: circular_dependency`
- Mixed transport: if a hook uses multiple transport mechanisms, emit separate items per transport with cross-reference
