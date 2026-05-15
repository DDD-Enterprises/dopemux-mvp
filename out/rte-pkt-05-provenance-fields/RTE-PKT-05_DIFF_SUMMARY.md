# RTE-PKT-05 Diff Summary

## In-scope runtime files

- `services/repo-truth-extractor/run_extraction_v5.py`
  - Imports provenance helper constants/builders.
  - Records provenance around existing contract-pipeline merge points.
  - Adds comparison-lane provenance after delegated comparison execution.
  - Writes a QA provenance companion during normalization when raw provenance exists.

- `services/repo-truth-extractor/lib/artifact_provenance.py`
  - New focused helper for redacted field-level and artifact-level provenance records.
  - Does not change provider schemas or provider dispatch.

## In-scope tests

- `services/repo-truth-extractor/tests/test_artifact_provenance_fields.py`
  - Local fixture tests for primary observed, deterministic parse repair, deterministic schema repair, sidefill, and provider repair provenance.
  - Monkeypatches provider dispatch.

## In-scope proof outputs

- All files under `out/rte-pkt-05-provenance-fields/`.

## Forbidden surfaces not changed

- Prompt files: not changed.
- Promptset YAML/model map: not changed.
- Provider route selection/client behavior: not changed.
- Config/compose/deployment files: not changed.
- Docs outside packet proof root: not changed.
