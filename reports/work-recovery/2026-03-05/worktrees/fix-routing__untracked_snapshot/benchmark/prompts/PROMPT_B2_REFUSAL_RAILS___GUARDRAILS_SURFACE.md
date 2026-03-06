# PROMPT_B2

## Goal
Produce `B2` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
Focus on boundary enforcement points, refusal rails, and concrete bypass evidence.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/90-adr/**`
- `.claude/**`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `BOUNDARY_INVENTORY.json`
- `BOUNDARY_PARTITIONS.json`
- `BOUNDARY_ENFORCEMENT_POINTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REFUSAL_GUARDRAILS_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REFUSAL_GUARDRAILS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B2`
    - `id_rule`: `REFUSAL_GUARDRAILS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `BOUNDARY_INVENTORY.json`, `BOUNDARY_PARTITIONS.json`, and `BOUNDARY_ENFORCEMENT_POINTS.json`; use enforcement points as the primary surface to discover refusal rails and guardrails.
2. For each enforcement point, determine whether it implements a refusal rail (explicit deny/reject/abort) or a guardrail (constrain/sanitize/limit); classify by `component` (service name) and `symbol` (function/class/decorator).
3. Extract the guard condition logic, rejection response format (HTTP status, error code, error message template), and any configurable thresholds or policy references with exact file:line evidence.
4. Scan `.claude/**` and `AGENTS.md` for declared behavioral guardrails, instruction-level constraints, and tool-use refusal policies; map each to the code-level enforcement point that implements it.
5. For each refusal rail, trace the trigger conditions and verify that the rejection is enforced at the boundary (not deferred to downstream); flag deferred rejections as `enforcement_gap`.
6. For each REFUSAL_GUARDRAILS_SURFACE item, populate `id` using `REFUSAL_GUARDRAILS_SURFACE:<stable-hash(path|symbol|name)>`, `component`, `symbol`, `path`, `line_range`, and `evidence` array.
7. Legacy Context is intent guidance only and is never evidence.
8. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
9. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
10. Attach evidence to every non-derived field and every relationship edge.
11. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
13. Emit exactly the declared outputs and no additional files.

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
- Do not invent endpoints, handlers, dependencies, env vars, commands, or policy claims.
- Do not infer intent from filenames alone; require direct textual/code evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Declared-but-unenforced guardrail: if `AGENTS.md` or `.claude/**` declares a behavioral constraint but no corresponding code enforcement point exists, emit with `status: declared_only` and `missing_evidence_reason`.
- Deferred rejection: if a refusal rail delegates rejection to a downstream service rather than rejecting at the boundary, flag with `enforcement_gap: true` and evidence of the delegation path.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_B2 — REFUSAL RAILS / GUARDRAILS SURFACE

TASK: Extract refusal rails and guardrails.

OUTPUTS:
	•	REFUSAL_GUARDRAILS_SURFACE.json
```
