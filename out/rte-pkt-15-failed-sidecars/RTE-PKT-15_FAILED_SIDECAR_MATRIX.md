# RTE-PKT-15 Failed Sidecar Matrix

This matrix is the summary view of `RTE-PKT-15_FAILED_SIDECAR_WRITER_LEDGER.md`.

| Surface | Status | Preserved context |
| --- | --- | --- |
| Worker exception `.FAILED.txt` | Sanitized through failed-sidecar text helper. | `phase`, `step_id`, `partition_id`, `failure_type`, provider/model request metadata. |
| Worker exception `.FAILED.json` | Sanitized through failed-sidecar payload helper. | Structured failure metadata and request metadata. |
| Parse failure `.FAILED.txt` | Raw response text sanitized before persistence. | Parse failure class, phase, step, partition, status code. |
| Parse failure `.FAILED.json` | Structured payload sanitized through failed-sidecar JSON path. | Failure class, status code, request metadata. |
| Schema failure `.FAILED.txt` | Raw schema-failed response text sanitized before persistence. | Schema gate failure label and context. |
| Schema failure `.FAILED.json` | Structured schema context sanitized through failed-sidecar JSON path. | Schema gate context, request metadata, failure class. |
| Batch missing-row `.FAILED.txt` | Direct writer uses failed-sidecar text helper. | Missing-row failure label. |
| Batch provider/parse `.FAILED.txt` | Direct writer uses failed-sidecar text helper. | Batch state, provider/model, batch id in paired JSON. |
| Batch terminal `.FAILED.txt` | Direct writer uses failed-sidecar text helper. | Terminal-state label. |
| Batch `.FAILED.json` | Direct writers use failed-sidecar-aware `write_json`. | Batch execution mode, provider/model, batch id, terminal status. |

## Out-of-scope observed path

`services/repo-truth-extractor/llm_runtime.py:1625` writes comparison-lane `.FAILED.txt` content directly. It is outside the packet allowlist and remains a follow-up `UNKNOWN`.
