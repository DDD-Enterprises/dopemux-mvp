# PROMPT_Q11

## Goal
Produce `Q11` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
Detect declared artifact collisions across the promptpack and emit a collision report that operators can use to stop unsafe norm overwrites before a live run.

## Inputs
- Source scope (scan these roots first):
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
  - `services/repo-truth-extractor/promptsets/v4/model_map.yaml`
  - `services/repo-truth-extractor/promptsets/v4/prompts/`
- Required upstream artifacts:
  - `Q_PROMPTPACK_DECLARED_OUTPUTS.json`
- Optional upstream artifacts:
  - `QA_PROMPT_COLLISIONS.json`
  - `QA_RUN_MANIFEST.json`
- Runner context artifacts:
  - `services/repo-truth-extractor/run_extraction_v5.py`
  - `services/repo-truth-extractor/prompts/phase_s/registry.json`
- Constraint:
  - Compute collisions from declared promptpack metadata and in-scope files only. Do not treat repository filesystem presence as proof of canonical writers.

## Outputs
- `QA_ARTIFACT_COLLISION_REPORT.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `QA_ARTIFACT_COLLISION_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q11`
    - `id_rule`: `QA_ARTIFACT_COLLISION_REPORT:<stable-hash(artifact_name|writers|risk)>`
    - `required_item_fields`: `id, artifact_name, writers, risk, recommendation, notes, evidence`
    - `required_registry_fields`: `path, line_range, id`
- Item shape:
  - `artifact_name`: emitted artifact under review
  - `writers`: array of `{phase, step_id, prompt_file}`
  - `risk`: collision class such as `overwrites_in_norm`, `shadowed_writer`, or `unknown_writer`
  - `recommendation`: one of `LATEST_WINS`, `APPEND_LEDGER`, `MERGE_BY_ID`, `MANUAL_REVIEW`
  - `notes`: deterministic explanatory strings
  - `evidence`: array of evidence objects proving each writer declaration

## Extraction Procedure
1. Load `Q_PROMPTPACK_DECLARED_OUTPUTS.json` and normalize each declared writer by `(phase, step_id, artifact_name)`.
2. Cross-check declarations against `promptset.yaml`, `artifacts.yaml`, and prompt files to confirm the writer list is supported by in-scope contract data.
3. Group rows by `artifact_name` and identify cases where two or more distinct steps declare the same output, or where registry metadata conflicts with prompt text.
4. Build one output item per collision candidate with deterministic `id`, sorted `writers`, sorted `notes`, and explicit `risk`.
5. When a writer cannot be proven from promptpack declarations, omit the unproven writer from `writers`, add a note containing `UNKNOWN`, and preserve evidence gaps.
6. Attach at least one evidence object to every collision item and to every non-derived writer entry.
7. Emit exactly `QA_ARTIFACT_COLLISION_REPORT.json` and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
