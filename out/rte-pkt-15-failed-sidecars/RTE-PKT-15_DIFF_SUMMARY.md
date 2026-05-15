# RTE-PKT-15 Diff Summary

## Runtime

- `services/repo-truth-extractor/output_safety.py`
  - Added private-key-block redaction.
  - Added common provider-token-prefix redaction.
  - Added `sanitize_failed_sidecar_text` as an explicit wrapper around output text sanitization.

- `services/repo-truth-extractor/run_extraction_v5.py`
  - Added `_is_failed_text_sidecar_path` and `write_failed_sidecar_text`.
  - Sanitized deferred `.FAILED.txt` writes when scheduling and again at persistence.
  - Replaced direct batch-watch `.FAILED.txt` writes with `write_failed_sidecar_text`.
  - Left JSON writers on existing `write_json` sanitizer path.

## Tests

- `services/repo-truth-extractor/tests/test_failed_sidecar_redaction.py`
  - Added local tests for worker exception, parse failure, schema failure, batch provider error, and batch terminal text redaction.
  - Tests use local fakes/monkeypatches and no provider calls.

- `services/repo-truth-extractor/tests/test_output_safety.py`
  - Added sanitizer regression coverage for provider-token-shaped text and private-key-block-shaped text while preserving safe SHA text.

## Scope boundary

No promptsets, model maps, structured-output contract files, provider route configs, compose/deployment files, or docs outside this proof root were changed.
