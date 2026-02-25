# PROMPT_X9

## Goal
Produce `X9` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/**`
- `README.md`
- Upstream normalized artifacts available to this step:
- `FEATURE_INDEX_INVENTORY.json`
- `FEATURE_INDEX_PARTITIONS.json`
- `FEATURE_SURFACE.json`
- `FEATURE_CODE_MAP.json`
- `FEATURE_DOC_MAP.json`
- `FEATURE_DEP_GRAPH.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_INDEX_MERGED.json`
- `FEATURE_INDEX_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_INDEX_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X9`
    - `id_rule`: `FEATURE_INDEX_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FEATURE_INDEX_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X9`
    - `id_rule`: `FEATURE_INDEX_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream X-phase artifacts (X0-X4 outputs) as specified in the inputs section. Merge Feature Index outputs into canonical artifacts by deterministic union keyed by stable feature identity keys (feature_id or name+service_id hash).
2. Run QA validation: check required schema fields, verify cross-references between surface/code-map/doc-map/dep-graph are consistent, and confirm no orphan features or dangling references exist. Report coverage by feature.
3. Emit coverage report: features with complete vs incomplete extraction across all X-phase dimensions, per-field completeness, unresolved mappings count, and schema violation list.
4. Structure the output with merged feature index, QA results by check type, coverage statistics, and an explicit UNKNOWN/gaps section for areas where QA cannot be completed due to missing inputs.
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
- Feature identity key collision during merge (different features with same computed ID): apply hash disambiguation and record the collision in QA output with evidence from both sources.
- Cross-reference between X-phase artifacts inconsistent (feature in surface but not in code map): record as `status: incomplete_extraction` with the missing dimension and evidence.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_X9_MERGE___QA

TASK: Merge Feature Index outputs and emit QA.

INPUTS:
- Raw/partition outputs from X0..X4.

OUTPUTS:
- FEATURE_INDEX_MERGED.json
- FEATURE_INDEX_QA.json

RULES:
- Deterministic merge only; no rescans.
- Deduplicate by stable feature identity keys.
- Report coverage, unresolved mappings, and schema/required-field checks.
```
