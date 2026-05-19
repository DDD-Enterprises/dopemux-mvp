# RTE-PKT-15 Failed Sidecar Writer Ledger

## In Scope

| Writer surface | Source | Writer type | Sanitizer status | Action |
| --- | --- | --- | --- | --- |
| Worker exception text sidecar | `services/repo-truth-extractor/run_extraction_v5.py:13673` via deferred `_op_write_text` | `.FAILED.txt` | Covered by `sanitize_failed_sidecar_text` before scheduling and again at persistence. | Hardened helper now uses the stronger failed-sidecar secret-shape path. |
| Worker exception JSON sidecar | `services/repo-truth-extractor/run_extraction_v5.py:13674` via deferred `_op_write_json` and `write_json` | `.FAILED.json` | Covered by `write_json`; `.FAILED.json` now uses `sanitize_payload_for_failed_sidecar`. | Hardened. |
| Payload-unshrinkable text sidecar | `services/repo-truth-extractor/run_extraction_v5.py:14051` via deferred `_op_write_text` | `.FAILED.txt` | Covered by central failed text sanitizer. | Hardened through shared helper. |
| Payload-unshrinkable JSON sidecar | `services/repo-truth-extractor/run_extraction_v5.py:14056` via deferred `_op_write_json` and `write_json` | `.FAILED.json` | Covered by failed sidecar payload sanitizer. | Hardened through shared helper. |
| Parse failure text sidecar | `services/repo-truth-extractor/run_extraction_v5.py:16087` via deferred `_op_write_text` | `.FAILED.txt` | Raw response text is sanitized before persistence. | Covered by targeted test. |
| Parse failure JSON sidecar | `services/repo-truth-extractor/run_extraction_v5.py:16088` via deferred `_op_write_json` and `write_json` | `.FAILED.json` | Structured payload is sanitized through failed sidecar payload sanitizer. | Covered by targeted test. |
| Schema failure text sidecar | `services/repo-truth-extractor/run_extraction_v5.py:16158` via deferred `_op_write_text` | `.FAILED.txt` | Raw response text is sanitized before persistence. | Covered by targeted test. |
| Schema failure JSON sidecar | `services/repo-truth-extractor/run_extraction_v5.py:16159` via deferred `_op_write_json` and `write_json` | `.FAILED.json` | Structured schema context is sanitized through failed sidecar payload sanitizer. | Covered by targeted test. |
| Batch missing-row text sidecar | `services/repo-truth-extractor/run_extraction_v5.py:19174` | `.FAILED.txt` | Direct writer uses `write_failed_sidecar_text`. | Covered by source inspection; text is local constant. |
| Batch missing-row JSON sidecar | `services/repo-truth-extractor/run_extraction_v5.py:19178` | `.FAILED.json` | Direct writer uses `write_json`, now failed-sidecar-aware. | Covered by source inspection. |
| Batch provider/parse text sidecar | `services/repo-truth-extractor/run_extraction_v5.py:19222` | `.FAILED.txt` | Direct writer uses `write_failed_sidecar_text`. | Covered by targeted test. |
| Batch provider/parse JSON sidecar | `services/repo-truth-extractor/run_extraction_v5.py:19226` | `.FAILED.json` | Direct writer uses `write_json`, now failed-sidecar-aware. | Covered by targeted test. |
| Batch terminal text sidecar | `services/repo-truth-extractor/run_extraction_v5.py:19421` | `.FAILED.txt` | Direct writer uses `write_failed_sidecar_text`. | Covered by targeted helper test. |
| Batch terminal JSON sidecar | `services/repo-truth-extractor/run_extraction_v5.py:19398` | `.FAILED.json` | Direct writer uses `write_json`, now failed-sidecar-aware. | Covered by source inspection. |

## Out Of Scope / Observed

| Writer surface | Source | Status |
| --- | --- | --- |
| Comparison-lane failed text sidecar | `services/repo-truth-extractor/llm_runtime.py:1625` | Out of packet allowlist. It still writes comparison failure text directly and remains a follow-up risk if this lane can carry secret-shaped provider or source text. |
| Batch retriever output/error files | `services/repo-truth-extractor/lib/batch_retriever.py` | Not `.FAILED.txt` or `.FAILED.json` sidecars. No provider retrieval was run. |
| Legacy v3 failed sidecar fixtures | `services/repo-truth-extractor/tests/fixtures/run_extraction_v3/` | Evidence fixtures only. Contents were not quoted in proof. |
