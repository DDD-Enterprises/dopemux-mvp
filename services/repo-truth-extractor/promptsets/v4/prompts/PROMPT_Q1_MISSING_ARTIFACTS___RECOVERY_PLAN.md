# PROMPT_Q1

## Goal
Produce `Q1` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `QA_MISSING_ARTIFACTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `QA_MISSING_ARTIFACTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q1`
    - `id_rule`: `QA_MISSING_ARTIFACTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `QA_RUN_MANIFEST.json` from Q0 and extract the list of missing artifacts. For each missing artifact, identify the producing step, the required inputs for that step, and whether those inputs are available.
2. Classify each missing artifact by recovery feasibility: `recoverable` (all inputs available, can re-run step), `blocked` (missing upstream dependency), or `manual` (requires human intervention or external data).
3. For recoverable artifacts, generate a recovery plan: the exact step command to re-run, the required inputs, and any prerequisites that must complete first.
4. Build a dependency-ordered recovery sequence: sort recovery actions so that upstream artifacts are recovered before downstream ones that depend on them.
5. Legacy Context is intent guidance only and is never evidence.
6. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
7. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
8. Attach evidence to every non-derived field and every relationship edge.
9. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
10. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
11. Emit exactly the declared outputs and no additional files.

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
- Missing artifact's producing step also has missing inputs: classify as `blocked` and list the transitive dependency chain that must be resolved first.
- Recovery plan would require re-running a step that modifies shared state: flag with `status: side_effect_risk` and recommend manual review.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_Q1 — MISSING ARTIFACTS / RECOVERY PLAN

TASK: Identify missing artifacts and propose a recovery plan.

OUTPUTS:
	•	QA_MISSING_ARTIFACTS.json
```
