# PROMPT_Z0

## Goal
Produce `Z0` outputs for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FREEZE_FILE_INDEX.json`
- `FREEZE_CHECKSUMS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FREEZE_FILE_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z0`
    - `id_rule`: `FREEZE_FILE_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FREEZE_CHECKSUMS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z0`
    - `id_rule`: `FREEZE_CHECKSUMS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan `extraction/**`, `docs/**`, and `services/repo-truth-extractor/**` as specified in the inputs section. Build a freeze file index by enumerating all norm and QA artifacts produced across all pipeline phases (A/H/D/C/E/W/B/G/Q/R/X/T/Z), recording file path, artifact name, writer step ID, and file size.
2. Compute SHA-256 checksums for every artifact in the freeze index. Record the checksum alongside the artifact metadata for downstream verification. Use deterministic file reading (binary mode, no encoding normalization).
3. Identify expected-but-missing artifacts by cross-referencing the `artifacts.yaml` manifest against actual files present. Record each missing artifact with its expected writer step ID and phase.
4. Structure the output with clear per-artifact index entries with checksums, a missing-artifacts section with evidence of expected locations, and an explicit UNKNOWN section for files that cannot be classified as pipeline artifacts.
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
- Artifact file is present but has zero bytes or is corrupted (checksum of empty content): record with `status: empty_or_corrupt` and the computed checksum; do not silently exclude.
- Expected phase directory does not exist (phase was not executed): record all expected artifacts for that phase as `status: phase_not_executed` with evidence from `artifacts.yaml`.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_Z0 — FREEZE INVENTORY / CHECKSUMS

TASK: Build an inventory and checksums for the handoff freeze.

OUTPUTS:
	•	FREEZE_FILE_INDEX.json
	•	FREEZE_CHECKSUMS.json
```
