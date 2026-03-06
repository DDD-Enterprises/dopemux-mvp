# PROMPT_Q2

## Goal
Produce `Q2` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
Focus on coverage, collisions, determinism drift, and recovery actions.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `services/repo-truth-extractor/**`
- `services/registry.yaml`
- `compose.yml`
- `docker-compose*.yml`
- Upstream normalized artifacts available to this step:
- `QA_RUN_MANIFEST.json`
- `QA_MISSING_ARTIFACTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `QA_PROMPT_COLLISIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `QA_PROMPT_COLLISIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q2`
    - `id_rule`: `QA_PROMPT_COLLISIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all merged phase artifacts; collect every item `id` across all artifacts into a global ID registry.
2. Detect duplicate IDs: identify items where the same `id` appears in multiple artifacts or within the same artifact; record each collision with both occurrences and their evidence.
3. Detect prompt collisions: identify cases where multiple prompts produce the same output artifact name; record the collision participants and their configuration.
4. Assess collision severity: classify as benign (intentional merge), problematic (data loss risk), or critical (silent overwrite).
5. For each QA_PROMPT_COLLISIONS item, populate `id`, collision type, affected artifacts, severity, and `evidence`.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

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
- Intentional collision: if two prompts intentionally produce the same artifact (merge prompts), flag with `collision_type: intentional_merge` and evidence from the artifact registry.
- Hash collision: if two different content items produce the same stable hash, flag with `collision_type: hash_collision` and full evidence of both items.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_Q2 — DUPLICATE IDS / PROMPT COLLISIONS

TASK: Detect duplicate IDs and prompt collisions.

OUTPUTS:
	•	QA_PROMPT_COLLISIONS.json
```
