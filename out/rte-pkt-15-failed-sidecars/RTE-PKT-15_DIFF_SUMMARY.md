# RTE-PKT-15 Diff Summary

## Runtime

- `services/repo-truth-extractor/output_safety.py`
  - Changed `sanitize_failed_sidecar_text` to use the stronger secret-shape sanitizer path.
  - Added `sanitize_payload_for_failed_sidecar` for structured failed sidecar payloads.
  - Preserved safe metadata behavior for environment-name fields and digest-shaped values.

- `services/repo-truth-extractor/run_extraction_v5.py`
  - Added `_is_failed_json_sidecar_path`.
  - Routed `.FAILED.json` writes through `sanitize_payload_for_failed_sidecar`.
  - Preserved existing `.FAILED.txt` writer names, sidecar filenames, failure classes, status codes, and request metadata shape.

## Tests

- `services/repo-truth-extractor/tests/test_output_safety.py`
  - Added coverage for generic long secret-shaped failed sidecar text and JSON payload values.
  - Verified safe environment-name and digest metadata remain visible.

- `services/repo-truth-extractor/tests/test_failed_sidecar_redaction.py`
  - Added direct `.FAILED.json` writer regression coverage for generic secret-shaped text in non-sensitive failure fields.

## Scope Boundary

No promptsets, schemas, model maps, route policies, retry logic, repair semantics, provider clients, provider batch operations, artifact schema redesign, or generated runtime sidecar fixtures were changed.
