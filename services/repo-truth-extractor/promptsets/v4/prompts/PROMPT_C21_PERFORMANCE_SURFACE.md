# PROMPT_C21

## Goal
Produce `C21` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract code-level performance risk surfaces across the repository: blocking calls in async contexts, N+1 query patterns, synchronous network calls inside event loops, unbounded loops, and other directly evidenced hotspots that can degrade runtime behavior.

## Inputs
- Source scope (scan these roots first):
  - `src/**`
  - `services/**`
  - `shared/**`
  - `scripts/**`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `API_DASHBOARD_SURFACE.json`
  - `WORKFLOW_RUNNER_SURFACE.json`
  - `SERVICE_ENTRYPOINTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PERFORMANCE_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"PERFORMANCE_SURFACE@v1","items":[...]}`
- Output contracts:
  - `PERFORMANCE_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C21`
    - `id_rule`: `PERFORMANCE_SURFACE:<stable-hash(path|symbol|risk_type)>`
    - `required_item_fields`: `id, risk_type, severity, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `risk_type` enum:
  - `blocking_call_in_async`
  - `sync_network_in_async`
  - `n_plus_one_query`
  - `unbounded_loop`
  - `repeated_expensive_scan`
- `severity` enum:
  - `low`
  - `medium`
  - `high`
  - `critical`

## Extraction Procedure
1. Load upstream code partitions, API surfaces, workflow surfaces, and entrypoints.
2. Scan async functions for blocking calls such as `time.sleep`, synchronous file IO, and other known blocking primitives.
3. Scan async handlers for synchronous HTTP clients, database clients, or subprocess execution that can block the event loop.
4. Scan loops around ORM queries, service calls, or repeated directory walks to find directly evidenced N+1 and repeated expensive scan patterns.
5. Scan for unbounded loops such as `while True`, polling loops without bounded backoff, or recursive retry patterns with no explicit cap.
6. Record the nearest protected symbol, the concrete risk type, and a severity based on the directly visible blast radius in the local code path.
7. Build deterministic IDs from `(path|symbol|risk_type)` and attach exact evidence excerpts that prove the risky call pattern.
8. Normalize by stable sort keys, deduplicate by ID, and emit exactly `PERFORMANCE_SURFACE.json`.

## Evidence Rules
- Each item must include the concrete call site or loop construct as evidence.
- Every evidence object must include exact `path`, `line_range`, and `excerpt` keys.
- If severity depends on the enclosing runtime surface, include a second evidence object showing the async handler, worker loop, or route registration.
- Keep excerpts exact and at or below 200 characters.
- Use `UNKNOWN` only when the risk is visible but the enclosing symbol or service cannot be recovered safely.

## Determinism Rules
- Do not emit profiler results, timing measurements, or environment-specific observations.
- Norm outputs MUST NOT contain `generated_at`, `timestamp`, `created_at`, `updated_at`, or `run_id`.
- Sort items by `(path, line_start, id)` and keep enum values stable.
- Deduplicate only when path, symbol, and risk type resolve to the same deterministic ID.
- Keep severity assignment stable by relying on directly visible context rather than dynamic speculation.

## Anti-Fabrication Rules
- Do not claim an N+1 query without evidence of repeated query issuance inside an iteration context.
- Do not label a call blocking in async unless the enclosing function is actually async or event-loop bound.
- Do not infer severity from naming or comments alone.
- Do not include generic performance advice or hypothetical optimizations.

## Failure Modes
- If a risk depends on external library internals not visible in the repo, record only the local risky invocation.
- If a helper function hides the expensive work, emit the caller and helper separately when both are evidenced.
- If a loop is intentionally long-running but bounded by explicit control state, classify it conservatively rather than as unbounded.
- If multiple risk types exist on one line, emit separate items when the risk classes are distinct.
