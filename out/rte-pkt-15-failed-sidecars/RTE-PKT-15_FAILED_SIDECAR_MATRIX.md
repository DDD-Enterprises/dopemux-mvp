# RTE-PKT-15 Failed Sidecar Matrix

## In-scope v5 writers

| Surface | Source | Coverage | Lineage preserved | Test coverage |
| --- | --- | --- | --- | --- |
| Worker exception `.FAILED.txt` | `run_extraction_v5.py` deferred `_op_write_text` and `_apply_write_ops` | CLOSED: `.FAILED.txt` text is sanitized before scheduling and again before persistence. | phase, step_id, partition_id, failure_type, provider, model_id, routing policy, route hop fields | `test_worker_exception_failed_sidecars_redact_secret_text` |
| Worker exception `.FAILED.json` | `run_extraction_v5.py` `write_json` | CLOSED: structured payload uses `write_json`, which calls `sanitize_payload_for_output`. | failure_type, status_code, request_meta, provider/model metadata | `test_worker_exception_failed_sidecars_redact_secret_text` |
| Parse failure `.FAILED.txt` | `run_extraction_v5.py` parse failure branch | CLOSED: raw response text flows through failed-sidecar text sanitizer. | phase, step_id, partition_id, status_code, provider/model via request_meta | `test_parse_failure_failed_sidecars_redact_raw_response_text` |
| Parse failure `.FAILED.json` | `run_extraction_v5.py` parse failure branch | CLOSED: `write_json` sanitizes structured payload. | failure_type, status_code, request_meta | `test_parse_failure_failed_sidecars_redact_raw_response_text` |
| Schema failure `.FAILED.txt` | `run_extraction_v5.py` schema gate branch | CLOSED: raw response text flows through failed-sidecar text sanitizer. | phase, step_id, partition_id, schema gate context | `test_schema_failure_failed_sidecars_redact_response_and_preserve_context` |
| Schema failure `.FAILED.json` | `run_extraction_v5.py` schema gate branch | CLOSED: `write_json` sanitizes structured schema context. | failure_type, status_code, schema_gate_context, request_meta | `test_schema_failure_failed_sidecars_redact_response_and_preserve_context` |
| Payload-unshrinkable `.FAILED.txt` | `run_extraction_v5.py` payload hard-cap branch | CLOSED through central deferred `.FAILED.txt` writer. | failure_type, phase, step_id, partition_id, payload sizing fields | Covered by central writer; no separate fixture generated |
| Payload-unshrinkable `.FAILED.json` | `run_extraction_v5.py` payload hard-cap branch | CLOSED through `write_json`. | failure_type, provider/model, status_code, sizing fields | Existing JSON sanitizer coverage |
| Batch missing-row `.FAILED.txt` | `run_extraction_v5.py` `run_batch_watch` | CLOSED: direct write now uses `write_failed_sidecar_text`. | phase, step_id, partition_id, batch job metadata in paired JSON | Static source check; text is local constant |
| Batch parse/provider `.FAILED.txt` | `run_extraction_v5.py` `run_batch_watch` | CLOSED: provider result text/error now uses `write_failed_sidecar_text`. | phase, step_id, partition_id, provider/model, batch_job_id in paired JSON | `test_batch_watch_failure_sidecars_redact_provider_error_text` |
| Batch terminal `.FAILED.txt` | `run_extraction_v5.py` `run_batch_watch` | CLOSED: terminal text now uses `write_failed_sidecar_text`. | terminal state text plus paired JSON request_meta | `test_failed_sidecar_text_writer_redacts_batch_terminal_text` |
| Batch `.FAILED.json` | `run_extraction_v5.py` `run_batch_watch` | CLOSED: direct structured sidecars use `write_json`. | execution_mode, provider, model_id, batch_provider, batch_job_id, failure_type | `test_batch_watch_failure_sidecars_redact_provider_error_text` |

## Out-of-scope observed writer

| Surface | Source | Coverage | Status |
| --- | --- | --- | --- |
| Comparison-lane `.FAILED.txt` | `services/repo-truth-extractor/llm_runtime.py:1342` | Not patched because packet allowed code paths did not include `llm_runtime.py`. | UNKNOWN / FOLLOW-UP REQUIRED if comparison-lane failed sidecars are in live proof scope |

## Notes

`services/repo-truth-extractor/lib/batch_retriever.py` writes downloaded provider output/error files, not `.FAILED.txt` or `.FAILED.json` sidecars. No provider retrieval operation was run.
