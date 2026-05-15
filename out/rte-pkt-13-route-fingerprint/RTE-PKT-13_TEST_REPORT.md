# RTE-PKT-13 Test Report

| Command | Exit | Result | Summary |
| --- | ---: | --- | --- |
| `pytest services/repo-truth-extractor/tests/test_route_fingerprint_static_identity.py -q` | 0 | PASS | 5 passed |
| `pytest services/repo-truth-extractor/tests/test_openrouter_xai_route_identity.py -q` | 0 | PASS | 6 passed |
| `pytest services/repo-truth-extractor/tests -k "routing_fingerprint or route_fingerprint or fingerprint" -q` | 0 | PASS | 8 passed |
| `pytest services/repo-truth-extractor/tests -k "openrouter and xai" -q` | 0 | PASS | 8 passed |
| `pytest services/repo-truth-extractor/tests -k "xai and metadata" -q` | 0 | PASS | 2 passed |
| `pytest services/repo-truth-extractor/tests/test_structured_output_provider_modes.py -q` | 0 | PASS | 3 passed |
| `pytest services/repo-truth-extractor/tests/test_llm_runtime_seam.py services/repo-truth-extractor/tests/test_provider_payload_redaction.py -q` | 0 | PASS | 12 passed |
| `pytest services/repo-truth-extractor/tests/test_v5_golden_fixture_smoke.py -q` | 0 | PASS | 1 passed |
| `pytest services/repo-truth-extractor/tests -k "proof_pack or proof or status" -q` | 0 | PASS | 25 passed |
| `pytest services/repo-truth-extractor/tests -k "risk and dashboard" -q` | 5 | NOT_RUN_NO_TESTS_SELECTED | No tests selected |
| `pytest services/repo-truth-extractor/tests -k "proof_contract or artifact_authority" -q` | 5 | NOT_RUN_NO_TESTS_SELECTED | No tests selected |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/llm_runtime.py` | 0 | PASS | Compilation passed |
| `python -m json.tool out/rte-pkt-13-route-fingerprint/RTE-PKT-13_MANIFEST.json >/dev/null` | 0 | PASS | Manifest JSON parsed |
| `git diff --check` | 0 | PASS | No whitespace errors in unstaged diff |
| `pre-commit run --files <changed files>` | 0 | PASS | Configured hooks passed for changed files |

All pytest runs emitted the existing pytest configuration warning for unknown `asyncio_mode`.
