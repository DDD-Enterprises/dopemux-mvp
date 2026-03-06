# PROMPT_B1

## Goal
Produce `B1` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `BOUNDARY_ENFORCEMENT_POINTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `BOUNDARY_ENFORCEMENT_POINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B1`
    - `id_rule`: `BOUNDARY_ENFORCEMENT_POINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `BOUNDARY_INVENTORY.json` and `BOUNDARY_PARTITIONS.json` to obtain the full boundary catalog; use these as the primary enumeration surface for enforcement point discovery.
2. For each boundary item in the inventory, scan the referenced `path` and `line_range` in source to locate explicit assertion statements, validation checks, guard clauses, and authorization decorators.
3. Classify each discovered enforcement point by type: input-validation, auth-check, rate-limit-guard, schema-assertion, invariant-check, or policy-gate; record the guard condition expression and the protected resource.
4. Trace call chains from each enforcement point to determine scope of protection: single endpoint, service-wide, or cross-service; attach call-graph evidence with file:line references.
5. Cross-reference enforcement points against `services/registry.yaml` to assign `service_id`; for points protecting shared middleware or libraries, assign to all consuming services.
6. For each BOUNDARY_ENFORCEMENT_POINTS item, populate `id` using `BOUNDARY_ENFORCEMENT_POINTS:<stable-hash(path|symbol|name)>`, `path`, `line_range`, and `evidence` array.
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
- Dead enforcement point: if a guard clause exists in code but is unreachable (commented out, behind always-false flag, or in dead code path), include it with `status: dead_code` and evidence of unreachability.
- Shared middleware ambiguity: if an enforcement point protects multiple services via shared code, emit one item per consuming service with shared evidence and note the duplication in `coverage_notes`.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_B1 — BOUNDARY ASSERTIONS / CODE ENFORCEMENT POINTS

TASK: Find boundary checks in code/config/docs (facts only).

OUTPUTS:
	•	BOUNDARY_ENFORCEMENT_POINTS.json
```
