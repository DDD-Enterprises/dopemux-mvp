# Implementation Notes

Packet: `RTE-PKT-05-PROVENANCE-FIELDS`

## Implemented

- Added `lib/artifact_provenance.py` for redacted field-level and artifact-level provenance records.
- Added provenance metadata to `run_extraction_v5.py` for:
  - deterministic parse repair
  - deterministic schema/canonicalization repair
  - deterministic path repair
  - provider targeted repair
  - provider envelope repair
  - sidefill
  - comparison lane
  - primary observed artifact summaries
- Added normalization-time QA rollup: `qa/<STEP>_ARTIFACT_PROVENANCE.json`.
- Added focused local tests in `test_artifact_provenance_fields.py`.

## Not changed

- Prompt text
- Promptset YAML
- Model map
- Provider route selection
- Provider clients
- Live extraction behavior
- Batch provider protocol

## Verification status

Targeted local tests passed before proof generation. Final whitespace/pre-commit/git-state checks are recorded in the final response and manifest if run after this file was written.
