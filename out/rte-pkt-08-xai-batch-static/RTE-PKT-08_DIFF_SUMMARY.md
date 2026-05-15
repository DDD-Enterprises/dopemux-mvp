# RTE-PKT-08 Diff Summary

## Files Touched

- `services/repo-truth-extractor/lib/batch_clients.py`
  - Added static proof markers.
  - Added terminal status classification.
  - Added proof-safe request metadata helper.
  - Added output/error JSONL fixture parsers with corrupt-line accounting.
  - Added custom_id correlation and missing-row proof helper.
  - Sanitized batch result `error` and `meta` fields returned by OpenAI-compatible result parsing.

- `services/repo-truth-extractor/lib/batch_retriever.py`
  - Preserves `output_file_id`, `error_file_id`, terminal status class, and local parse reports when downloaded files are available.
  - Does not add new provider retrieval behavior.

- `services/repo-truth-extractor/run_extraction_v5.py`
  - Treats `expired` as a terminal batch status.
  - Adds `batch_status` and `batch_status_class` to batch-watch request metadata.

- `services/repo-truth-extractor/tests/test_rte_pkt_08_batch_static_proof.py`
  - Adds local fixture tests for output JSONL, error JSONL, missing rows, partial failure, terminal statuses, corrupt-line thresholds, request metadata, and no-provider-call safety.

- `services/repo-truth-extractor/tests/test_batch_retriever.py`
  - Extends existing fake-client retrieval coverage to prove output file IDs remain visible and live-downloaded parse reports are not mislabeled as static-only.

- `out/rte-pkt-08-xai-batch-static/*`
  - Packet proof artifacts only.

## Boundary Check

No prompt files, promptset YAML, model map YAML, route selection files, config, compose files, pricing files, or docs outside the allowed proof output root were edited.
