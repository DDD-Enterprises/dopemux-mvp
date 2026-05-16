# RTE-PKT-14 Test Report

## Required Validation

| Command | Result |
| --- | --- |
| `pytest services/repo-truth-extractor/tests/test_pricing_surface_static_identity.py -q` | PASS exit=0, 6 passed |
| `pytest services/repo-truth-extractor/tests/test_openrouter_xai_route_identity.py -q` | PASS exit=0, 6 passed |
| `pytest services/repo-truth-extractor/tests/test_route_fingerprint_static_identity.py -q` | PASS exit=0, 5 passed |
| `pytest services/repo-truth-extractor/tests/test_pricing_catalog.py services/repo-truth-extractor/tests/test_pricing_coverage.py services/repo-truth-extractor/tests/test_profile_review_packets.py -q` | PASS exit=0, 5 passed |
| `pytest services/repo-truth-extractor/tests -k "pricing or spend or cost" -q` | PASS exit=0, 44 passed, 1 skipped |
| `pytest services/repo-truth-extractor/tests -k "openrouter and xai" -q` | PASS exit=0, 11 passed |
| `pytest services/repo-truth-extractor/tests -k "xai and metadata" -q` | PASS exit=0, 10 passed |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/llm_runtime.py` | PASS exit=0 |

## Optional Validation

| Command | Result |
| --- | --- |
| `pytest services/repo-truth-extractor/tests -k "proof_pack or proof or status" -q` | PASS exit=0, 43 passed |
| `pytest services/repo-truth-extractor/tests -k "risk and dashboard" -q` | PASS exit=0, 9 passed |
| `pytest services/repo-truth-extractor/tests -k "proof_contract or artifact_authority" -q` | PASS exit=0, 10 passed |

## Shared Test Warning

All pytest runs emitted the existing warning `Unknown config option: asyncio_mode`. The broad pricing/spend/cost selector skipped one unrelated CLI test because `dopemux` was not importable in that test context.

## Final Hygiene

| Command | Result |
| --- | --- |
| `python -m json.tool out/rte-pkt-14-pricing-visibility/RTE-PKT-14_MANIFEST.json >/dev/null` | PASS exit=0 |
| `python -m json.tool out/rte-pkt-14-pricing-visibility/RTE-PKT-14_TASK_PACKET.json >/dev/null` | PASS exit=0 |
| `jsonschema validation for out/rte-pkt-14-pricing-visibility/RTE-PKT-14_TASK_PACKET.json` | PASS exit=0 |
| `git diff --check` | PASS exit=0 |
| `git diff --cached --check` | PASS exit=0, no staged files |
| `pre-commit run --files <changed files>` | PASS exit=0 |
