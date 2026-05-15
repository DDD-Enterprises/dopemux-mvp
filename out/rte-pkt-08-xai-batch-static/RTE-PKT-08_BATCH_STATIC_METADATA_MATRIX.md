# RTE-PKT-08 Batch Static Metadata Matrix

## Scope

This packet closes static fixture proof gaps only. It does not prove live xAI/OpenAI-compatible batch behavior.

## Matrix

| Surface | Proof path | Fields now proof-visible | Status |
| --- | --- | --- | --- |
| Request row metadata | `build_batch_request_static_metadata` in `services/repo-truth-extractor/lib/batch_clients.py` | `custom_id`, method, URL, requested model, messages-present boolean, response format type, provider, structured-output mode, phase, step, partition | STATIC_FIXTURE_VALIDATED |
| Output JSONL parser | `parse_openai_compatible_batch_output_jsonl` | `custom_id`, response status, response/body presence, response id, returned model, finish reason, usage, failure type, parse status, schema status, redaction status | STATIC_FIXTURE_VALIDATED |
| Error JSONL parser | `parse_openai_compatible_batch_error_jsonl` | `custom_id`, error type, code, redacted message, status code, failure type, redaction status | STATIC_FIXTURE_VALIDATED |
| Corrupt line handling | shared JSONL parser in `batch_clients.py` | total lines, blank lines, valid rows, discarded lines, corrupt lines, redacted discarded-line previews, 5 percent threshold status | STATIC_FIXTURE_VALIDATED |
| Custom ID correlation | `build_openai_compatible_batch_static_proof` | request count, result count, error count, missing row count, missing IDs, duplicate output/error IDs, partial failure, full success | STATIC_FIXTURE_VALIDATED |
| Terminal status distinction | `classify_batch_terminal_status`; v5 `_batch_terminal_state` now includes `expired` | completed/succeeded/done as success; failed, expired, cancelled/canceled, timeout as distinct terminal classes | STATIC_FIXTURE_VALIDATED |
| Retriever file IDs | `retrieve_openai_compatible_batch` in `batch_retriever.py` | `output_file_id`, `error_file_id`, `status_class`, `terminal`, local output/error parse report when files are available | STATIC_METADATA_HARDENED |
| v5 batch watch failure metadata | `run_batch_watch` in `run_extraction_v5.py` | `batch_status`, `batch_status_class` in success/failure request metadata; `expired` handled as terminal | STATIC_METADATA_HARDENED |
| Live provider behavior | none | submit/poll/retrieve/cancel behavior, provider file lifecycle, pagination/completeness, ZDR/retention | LIVE_VALIDATION_REQUIRED |

## Distinctions Preserved

- Local fixture parsing is separate from provider batch submission, polling, retrieval, and cancellation.
- Output JSONL and error JSONL use separate parser entrypoints.
- Missing result rows are hard failures via `missing_rows_are_hard_failure=true`.
- Partial failure is distinct from full success via `partial_failure` and `full_success`.
- Terminal failed, expired, cancelled, timeout, and completed states are classified separately.
- Static parser confidence is marked with `NOT_LIVE_VALIDATED` and `LIVE_VALIDATION_REQUIRED`.
