# PROMPT_Z9

## Goal
Produce `Z9` outputs for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
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
- `OPUS_INPUT_MANIFEST.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FREEZE_MANIFEST.json`
- `FREEZE_README.md`
- `FREEZE_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FREEZE_MANIFEST.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z9`
    - `id_rule`: `FREEZE_MANIFEST:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, artifact_name, sha256, writer_step_id, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FREEZE_README.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `Z9`
    - `id_rule`: `FREEZE_README:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `FREEZE_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z9`
    - `id_rule`: `FREEZE_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream Z-phase artifacts (Z0-Z2 outputs) as specified in the inputs section. Produce a deterministic freeze handoff manifest including SHA-256 for every file in phase `norm/` and `qa/` outputs across all phases (A/H/D/C/E/W/B/G/Q/R/X/T/Z), plus prompt corpus fingerprints for active `PROMPT_*.md` files.
2. Record missing expected artifacts and failure counts by phase. Cross-reference against `artifacts.yaml` to ensure completeness. Generate `FREEZE_README.md` with deterministic verification commands that a downstream consumer can run to validate the freeze.
3. Run final QA: verify all checksums are consistent with file contents, all cross-references resolve, no duplicate artifact IDs exist, and the manifest is self-consistent. Emit `FREEZE_QA.json` with pass/fail per check.
4. Structure the output with the complete freeze manifest, README with verification commands, QA results, and an explicit UNKNOWN section for any artifacts or checks that could not be completed.
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
- Final QA discovers inconsistency between manifest and actual files on disk: emit `FREEZE_QA.json` with `status: FAIL` for affected checks and detailed evidence of each inconsistency.
- Prompt corpus fingerprints show uncommitted modifications to active prompt files: record the modified files with their dirty checksums and flag with `status: uncommitted_changes`.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_Z9 — FREEZE MANIFEST / CHECKSUMS

TASK: Produce a deterministic freeze handoff manifest with verification instructions and QA.

OUTPUTS:
- FREEZE_MANIFEST.json
- FREEZE_README.md
- FREEZE_QA.json

Rules:
- Include SHA-256 for every file in phase `norm/` and `qa/` outputs for A/H/D/C/E/W/B/G/Q/R/X/T/Z when present.
- Include prompt corpus fingerprint entries for active `services/repo-truth-extractor/prompts/v3/PROMPT_*.md` files.
- Record missing expected artifacts and failure counts by phase.
- `FREEZE_README.md` must document deterministic verification commands.
```
