# PROMPT_Q3

## Goal
Produce `Q3` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `QA_NORM_DRIFT_REPORT.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `QA_NORM_DRIFT_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q3`
    - `id_rule`: `QA_NORM_DRIFT_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Compare raw vs normalized artifact pairs: for each step that produces both raw and norm outputs, compare item counts, field completeness, and schema compliance. Record drift where norm count differs from raw count.
2. Detect truncation: identify normalized artifacts where items appear to have been truncated (fields ending with `...`, missing `evidence` arrays, or `excerpt` fields shorter than expected). Flag with `status: suspected_truncation`.
3. Validate schema consistency: check that every normalized artifact conforms to its declared schema contract (`kind`, `merge_strategy`, `id_rule`, `required_item_fields`). Record violations.
4. Generate `QA_NORM_DRIFT_REPORT.json` with per-artifact comparison: raw_count, norm_count, drift_percentage, schema_violations, truncation_flags, and overall health status.
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
- Raw artifact exists but corresponding norm artifact is missing: emit with `status: normalization_failed` and the raw artifact path as evidence.
- Schema contract itself is ambiguous or contradictory: emit with `status: schema_ambiguity` and cite the conflicting contract fields.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_Q3 — DRIFT DETECTION / NORM DIFFS

TASK: compare raw vs norm counts + schema sanity + truncation flags.

OUTPUTS:
	•	QA_NORM_DRIFT_REPORT.json
```
