# PROMPT_Z2

## Goal
Produce `Z2` outputs for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `FREEZE_FILE_INDEX.json`
- `FREEZE_CHECKSUMS.json`
- `PROOF_PACK.md`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `OPUS_INPUT_MANIFEST.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `OPUS_INPUT_MANIFEST.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z2`
    - `id_rule`: `OPUS_INPUT_MANIFEST:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, artifact_name, sha256, writer_step_id, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream Z-phase artifacts (freeze index, checksums, proof pack) as specified in the inputs section. Generate a deterministic export bundle manifest (`OPUS_INPUT_MANIFEST.json`) listing every artifact that Opus and Codex consumers need, with `artifact_name`, `sha256`, `writer_step_id`, `phase`, and `evidence` for each entry.
2. Organize the manifest by consumer: which artifacts are needed for Opus synthesis (S-phase inputs) vs Codex implementation (T-phase packet inputs). Include dependency ordering so consumers can load artifacts in the correct sequence.
3. Validate manifest completeness against `artifacts.yaml`: every artifact declared as an Opus/Codex input must appear in the manifest with a valid checksum. Record missing entries with reasons.
4. Structure the output with clear per-artifact manifest entries, consumer groupings, dependency order, and an explicit UNKNOWN section for artifacts that cannot be verified or located.
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
- Manifest references an artifact whose checksum differs from `FREEZE_CHECKSUMS.json`: flag as `status: checksum_mismatch` with both checksums and do not include in validated bundle.
- Consumer dependency ordering contains a cycle (artifact A needs B which needs A): document the cycle and emit a best-effort load order with the cycle broken at the lowest-priority edge.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_Z2 — OPUS INPUT BUNDLE / MANIFEST

TASK: Generate a deterministic export bundle manifest for Opus + Codex.

OUTPUTS:
	•	OPUS_INPUT_MANIFEST.json
```
