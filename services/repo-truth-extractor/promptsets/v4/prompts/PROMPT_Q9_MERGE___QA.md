# PROMPT_Q9

## Goal
Produce `Q9` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
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
- `QA_PROMPT_COLLISIONS.json`
- `QA_NORM_DRIFT_REPORT.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PIPELINE_DOCTOR_REPORT.json`
- `QA_SERVICE_COVERAGE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `PIPELINE_DOCTOR_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q9`
    - `id_rule`: `PIPELINE_DOCTOR_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `QA_SERVICE_COVERAGE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `single_payload`
    - `canonical_writer_step_id`: `Q9`
    - `id_rule`: `QA_SERVICE_COVERAGE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`

## Extraction Procedure
1. Load all Q-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all QA_* artifacts into PIPELINE_DOCTOR_REPORT using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all Q-Phase artifacts present, coverage complete, sort order deterministic; emit QA_SERVICE_COVERAGE
4. Cross-check coverage: verify every inventory item has corresponding extraction entries
5. For each output item, populate `id`, required fields, and `evidence` per schema contracts
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
- Missing Q-Phase artifact: if any upstream artifact is absent, proceed with available and record gap with `status: incomplete_merge`
- Suspicious gap: if an inventory item has no extraction entry, flag with `status: uncovered`

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_Q9 — Pipeline doctor merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge pipeline doctor outputs into a single report.

OUTPUTS:
  • PIPELINE_DOCTOR_REPORT.json

RULES:
  • Maintain deterministic ordering and mark any empty sections explicitly.
```
