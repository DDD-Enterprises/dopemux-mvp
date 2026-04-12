# PROMPT_C19

## Goal
Produce `C19` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract concrete error-handling patterns across the codebase: targeted exception handling, broad exception swallowing, reraises, retry wrappers, and operator-visible failure pathways in API, CLI, workflow, and background execution code.

## Inputs
- Source scope (scan these roots first):
  - `src/**`
  - `services/**`
  - `scripts/**`
  - `shared/**`
  - `plugins/**`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `API_DASHBOARD_SURFACE.json`
  - `WORKFLOW_RUNNER_SURFACE.json`
  - `TASKX_INTEGRATION_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `ERROR_HANDLING_PATTERNS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"ERROR_HANDLING_PATTERNS@v1","items":[...]}`
- Output contracts:
  - `ERROR_HANDLING_PATTERNS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C19`
    - `id_rule`: `ERROR_HANDLING_PATTERNS:<stable-hash(path|symbol|exception_type|handling_style)>`
    - `required_item_fields`: `id, handling_style, protected_symbol, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `handling_style` enum:
  - `targeted_catch`
  - `broad_catch`
  - `bare_except`
  - `reraise`
  - `swallow`
  - `retry_wrapper`
  - `fallback_return`

## Extraction Procedure
1. Load upstream code, API, workflow, and task integration artifacts; use the code partition as scan surface.
2. Scan for `try` / `except` blocks, `except Exception`, bare `except:`, and wrappers that convert exceptions into status objects or warnings.
3. Capture the protected symbol or function context, the exception types handled, and whether the handler reraises, swallows, retries, returns a fallback, or logs-and-continues.
4. Scan for retry decorators or retry helpers to distinguish deliberate retry behavior from silent swallow behavior.
5. Scan API handlers for `HTTPException`, custom error envelopes, and broad exception conversion that can hide failure classes from operators.
6. Scan CLI and workflow runners for patterns that catch subprocess, IO, or network failures and continue execution.
7. Build deterministic IDs from `(path|symbol|exception_type|handling_style)` and attach exact excerpts that prove both the catch site and the handling behavior.
8. Normalize items by stable sort keys, deduplicate by ID, and emit exactly `ERROR_HANDLING_PATTERNS.json`.

## Evidence Rules
- Every item must include evidence for the catch site and the handling action.
- `line_range` should cover the smallest span that still proves the behavior.
- Every evidence object must carry exact `path`, `line_range`, and `excerpt` keys.
- If the handler delegates to another helper, include evidence for both the delegation site and the helper.
- When a code path is ambiguous, set the relevant value to `UNKNOWN` and preserve the evidence gap in the item.

## Determinism Rules
- Exclude timestamps and transient runtime status from norm artifacts.
- Sort `items` by `(path, line_start, id)` and keep enum values stable.
- Merge duplicates by ID and union evidence deterministically.
- Prefer the lexically smallest non-empty scalar when multiple equivalent values remain after evidence review.

## Anti-Fabrication Rules
- Do not label a handler as `swallow` if it logs and reraises; prove the final behavior.
- Do not infer retry semantics from helper names alone; require evidence of retry control flow or retry library usage.
- Do not claim operator-visible error shaping unless the route, CLI, or workflow surface is evidenced.
- Do not collapse multiple distinct handlers into one item when they protect different symbols or failure classes.

## Failure Modes
- If macros, decorators, or generated wrappers hide the actual exception behavior, emit only the directly evidenced layer and mark downstream behavior `needs_review`.
- If a single block handles multiple exceptions with different actions, emit separate items when the actions are distinguishable.
- If fallback behavior is spread across nested helpers, keep the item partial instead of inventing a unified handling style.
- If the protected symbol cannot be determined from local context, preserve `UNKNOWN` with the nearest enclosing function evidence.
