# RTE-PKT-12 Test Report

All executed tests were local/static. No live extraction, provider preflight, provider batch operation, or provider credential access was run.

| Command | Exit | Result |
| --- | ---: | --- |
| `pytest services/repo-truth-extractor/tests/test_openrouter_xai_route_identity.py -q` | 0 | PASS, 6 passed |
| `pytest services/repo-truth-extractor/tests/test_structured_output_provider_modes.py -q` | 0 | PASS, 3 passed |
| `pytest services/repo-truth-extractor/tests/test_prescan_provider_catalog.py -q` | 0 | PASS, 36 passed |
| `pytest services/repo-truth-extractor/tests/test_llm_runtime_seam.py services/repo-truth-extractor/tests/test_provider_payload_redaction.py -q` | 0 | PASS, 12 passed |
| `pytest services/repo-truth-extractor/tests -k 'openrouter and xai' -q` | 0 | PASS, 6 passed |
| `pytest services/repo-truth-extractor/tests -k 'xai and metadata' -q` | 0 | PASS, 2 passed |
| `pytest services/repo-truth-extractor/tests -k 'structured_output or provider_modes' -q` | 0 | PASS, 5 passed |
| `pytest services/repo-truth-extractor/tests/test_pricing_catalog.py services/repo-truth-extractor/tests/test_pricing_coverage.py services/repo-truth-extractor/tests/test_profile_review_packets.py -q` | 0 | PASS, 5 passed |
| `pytest services/repo-truth-extractor/tests -k 'risk and dashboard' -q` | 5 | NOT_RUN_NO_TESTS_SELECTED |
| `pytest services/repo-truth-extractor/tests -k 'proof_contract or artifact_authority' -q` | 5 | NOT_RUN_NO_TESTS_SELECTED |
| `python -m py_compile services/repo-truth-extractor/llm_runtime.py services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/lib/structured_output_contracts.py services/repo-truth-extractor/lib/prescan/provider_catalog.py` | 0 | PASS |
| `python -m json.tool out/rte-pkt-12-openrouter-xai/RTE-PKT-12_MANIFEST.json >/dev/null` | 0 | PASS |
| `git diff --check` | 0 | PASS |
| `git status --short --branch` | 0 | PASS, only allowed code/test files and packet proof output root changed |

Common warning: pytest reported `PytestConfigWarning: Unknown config option: asyncio_mode`. This appears pre-existing and did not fail the targeted tests.
