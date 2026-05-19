# RTE-PKT-15 Test Report

## PASS

| Command | Result |
| --- | --- |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/output_safety.py` | PASS, exit code 0 |
| `pytest services/repo-truth-extractor/tests/test_output_safety.py -q` | PASS, 7 passed; warning for unknown `asyncio_mode` |
| `pytest services/repo-truth-extractor/tests/test_failed_sidecar_redaction.py -q` | PASS, 6 passed; warning for unknown `asyncio_mode` |
| `pytest services/repo-truth-extractor/tests/test_provider_payload_redaction.py -q` | PASS, 4 passed; warning for unknown `asyncio_mode` |
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py -q` | PASS, 39 passed; warning for unknown `asyncio_mode` |
| `pytest services/repo-truth-extractor/tests/test_batch_clients_integration.py -q` | PASS, 7 passed; warning for unknown `asyncio_mode` |
| `pytest services/repo-truth-extractor/tests/test_strict_passthrough_attestations.py -q` | PASS, 5 passed; warning for unknown `asyncio_mode` |
| `git diff --check` | PASS, exit code 0 |
| `git diff --name-only origin/main...HEAD` allowlist check | PASS, only RTE-PKT-15 allowlisted files remain |
| `pre-commit run --files ...` | PASS, exit code 0; configured hooks passed or skipped where not applicable |

## NOT_RUN / Substituted

| Packet command | Observed status | Substitution |
| --- | --- | --- |
| `pytest services/repo-truth-extractor/tests/test_batch_clients.py -q` | File absent; direct command returned pytest exit code 4. | `pytest services/repo-truth-extractor/tests/test_batch_clients_integration.py -q` passed. |
| `pytest services/repo-truth-extractor/tests/test_strict_passthrough.py -q` | File absent; direct command returned pytest exit code 4. | `pytest services/repo-truth-extractor/tests/test_strict_passthrough_attestations.py -q` passed. |
| Live extraction / provider calls / provider batch operations | Forbidden by packet. | Not run. |

## Secret-Shape Scan

- Literal packet grep over the broad RTE test tree reports expected positives in sanitizer literals, synthetic test literals, and legacy fixture paths. Matched contents were not copied into proof.
- Safe path/count scan over touched files found no matches in `run_extraction_v5.py` or `test_failed_sidecar_redaction.py`; `output_safety.py` and `test_output_safety.py` each contain one deliberate private-key-pattern literal used by the sanitizer/test.

## Provider Boundary

No validation command used provider credentials, submitted provider batch jobs, polled provider batch jobs, retrieved provider batch jobs, cancelled provider batch jobs, or ran live extraction.
