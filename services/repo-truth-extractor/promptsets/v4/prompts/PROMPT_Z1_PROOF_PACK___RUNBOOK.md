# PROMPT_Z1

## Goal
Produce `Z1` outputs for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `FREEZE_FILE_INDEX.json`
- `FREEZE_CHECKSUMS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PROOF_PACK.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `PROOF_PACK.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `Z1`
    - `id_rule`: `PROOF_PACK:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load `FREEZE_FILE_INDEX.json` and `FREEZE_CHECKSUMS.json` as specified in the inputs section. Generate a proof pack snapshot documenting: pipeline execution evidence (which phases completed, artifact counts per phase), verification commands for each checksum, and a step-by-step runbook for reproducing the extraction.
2. For each phase, summarize: number of artifacts produced, QA pass/fail status (if QA artifact exists), and any known issues from QA reports. Include the exact commands needed to verify checksums.
3. Document the deterministic reproduction procedure: required inputs, environment setup, execution sequence, and expected outputs. Include version pinning for tools and dependencies.
4. Structure the output as a markdown proof pack with clear sections for execution evidence, verification runbook, reproduction procedure, and an explicit UNKNOWN section for phases where proof evidence is incomplete.
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
- QA artifact for a phase reports failures but the phase artifacts are still included in freeze: document the QA failures in the proof pack with severity and include conditional verification steps.
- Reproduction procedure depends on tools or versions not pinned in repo: record as `reproduction_risk: version_unpinned` with the tool names and available version evidence.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_Z1 — PROOF PACK / RUNBOOK

TASK: Generate a proof pack snapshot and runbook.

OUTPUTS:
	•	PROOF_PACK.md
```
