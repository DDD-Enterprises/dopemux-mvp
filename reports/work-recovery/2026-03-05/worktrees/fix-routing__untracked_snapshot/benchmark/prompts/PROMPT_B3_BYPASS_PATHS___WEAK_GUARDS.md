# PROMPT_B3

## Goal
Produce `B3` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
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
- `REFUSAL_GUARDRAILS_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `BOUNDARY_BYPASS_RISKS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `BOUNDARY_BYPASS_RISKS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B3`
    - `id_rule`: `BOUNDARY_BYPASS_RISKS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `BOUNDARY_INVENTORY.json`, `BOUNDARY_PARTITIONS.json`, `BOUNDARY_ENFORCEMENT_POINTS.json`, and `REFUSAL_GUARDRAILS_SURFACE.json`; use enforcement points and guardrails as the primary surfaces to discover bypass paths.
2. For each enforcement point and guardrail, search for alternate code paths that reach the protected resource without triggering the guard: check for missing decorator applications, conditional guard skips (`if debug`, `if env == test`), and unprotected duplicate routes.
3. Identify weak guards: guards with overly broad exception handlers that swallow authorization failures, guards with hardcoded bypass tokens or admin overrides, and guards with time-of-check-to-time-of-use (TOCTOU) gaps.
4. For each bypass risk, assess severity (critical|high|medium|low) based on: sensitivity of the protected resource, ease of exploitation, and whether the bypass is intentional (documented admin override) vs unintentional.
5. Cross-reference each bypass risk with the owning service from `services/registry.yaml` and the specific enforcement point it circumvents; populate `location` with the repo-relative path and line range of the bypass.
6. For each BOUNDARY_BYPASS_RISKS item, populate `id` using `BOUNDARY_BYPASS_RISKS:<stable-hash(path|symbol|name)>`, `risk` (description), `severity`, `location`, and `evidence` array.
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
- Intentional bypass misclassification: if an admin override or debug bypass is documented as intentional but lacks explicit evidence of authorization controls, emit with `severity: medium` and `status: needs_review` noting the documentation gap.
- Incomplete call-graph trace: if static analysis cannot fully resolve a bypass path due to dynamic dispatch, reflection, or plugin loading, emit the partial path with `status: needs_review` and `coverage_notes` explaining the analysis limitation.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_B3 — BYPASS PATHS / WEAK GUARDS

TASK: Identify bypass paths and weak guards.

RULE: only report bypass when evidenced by an alternate path or missing check near a sensitive operation.

OUTPUTS:
	•	BOUNDARY_BYPASS_RISKS.json
```
