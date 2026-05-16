# RTE-PKT-15 Test Report

## Required Validation

| Command | Result |
|---|---|
| `python -m json.tool out/rte-pkt-15-artifact-consumer-compat/RTE-PKT-15_TASK_PACKET.json >/dev/null` | PASS exit=0 |
| JSON schema validation for `RTE-PKT-15_TASK_PACKET.json` against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | PASS exit=0 |
| `pytest services/repo-truth-extractor/tests/test_artifact_consumer_static_compatibility.py -q` | PASS exit=0, 5 tests |
| `pytest services/repo-truth-extractor/tests/test_openrouter_xai_route_identity.py -q` | PASS exit=0, 6 tests |
| `pytest services/repo-truth-extractor/tests/test_route_fingerprint_static_identity.py -q` | PASS exit=0, 5 tests |
| `pytest services/repo-truth-extractor/tests/test_pricing_surface_static_identity.py -q` | PASS exit=0, 6 tests |
| `pytest services/repo-truth-extractor/tests/test_pricing_catalog.py services/repo-truth-extractor/tests/test_pricing_coverage.py services/repo-truth-extractor/tests/test_profile_review_packets.py -q` | PASS exit=0, 5 tests |
| `pytest services/repo-truth-extractor/tests -k "proof_pack or proof or status" -q` | PASS exit=0, 45 tests |
| `pytest services/repo-truth-extractor/tests -k "routing_fingerprint or route_fingerprint or fingerprint" -q` | PASS exit=0, 8 tests |
| `pytest services/repo-truth-extractor/tests -k "pricing or spend or cost" -q` | PASS exit=0, selected tests passed with 1 skip (`test_truth_run_cli.py` dopemux import context) |
| `pytest services/repo-truth-extractor/tests -k "openrouter and xai" -q` | PASS exit=0, 12 tests |
| `pytest services/repo-truth-extractor/tests -k "xai and metadata" -q` | PASS exit=0, 10 tests |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/llm_runtime.py` | PASS exit=0 |
| `python -m json.tool out/rte-pkt-15-artifact-consumer-compat/RTE-PKT-15_MANIFEST.json >/dev/null` | PASS exit=0 |
| `git diff --check` | PASS exit=0 |
| `git diff --cached --check` | PASS exit=0 |
| `pre-commit run --files <changed files>` | PASS exit=0 |

All pytest runs emitted the existing `PytestConfigWarning: Unknown config option: asyncio_mode` warning from repository pytest configuration. It did not fail the selected tests.

## Optional Selectors

| Command | Result |
|---|---|
| `pytest services/repo-truth-extractor/tests -k "dashboard or run_dashboard" -q` | PASS exit=0, 11 tests |
| `pytest services/repo-truth-extractor/tests -k "failure_index or coverage_rollup" -q` | NOT_RUN_NO_TESTS_SELECTED, pytest exit=5 |
| `pytest services/repo-truth-extractor/tests -k "proof_contract or artifact_authority" -q` | PASS exit=0, 11 tests |
| `pytest services/repo-truth-extractor/tests -k "risk and dashboard" -q` | PASS exit=0, 10 tests |

## Provider Safety

No command in this packet ran live extraction, provider preflight, provider batch submission/poll/retrieve/cancel, or provider client calls. The new static test module monkeypatches provider-client entrypoints to raise on the no-provider-call path.
