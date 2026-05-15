# RTE-PKT-04 Test Report

## Commands

| Command | Result | Notes |
| --- | --- | --- |
| `pytest services/repo-truth-extractor/tests/test_prescan_influence_labels.py -q` | PASS | 5 passed. Pytest warned about unknown config option `asyncio_mode`. |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/lib/intelligence_router.py services/repo-truth-extractor/lib/prescan/engine.py` | PASS | Runtime files compile. |
| `pytest services/repo-truth-extractor/tests/test_prescan_import_staleness.py services/repo-truth-extractor/tests/test_prescan_v5_integration.py services/repo-truth-extractor/tests/test_router_runtime_integration.py services/repo-truth-extractor/tests/test_prescan_consumers.py -q` | PASS | 18 passed. Pytest warned about unknown config option `asyncio_mode`. |
| `pytest services/repo-truth-extractor/tests -k 'prescan and influence' -q` | PASS | 6 passed. Pytest warned about unknown config option `asyncio_mode`. |
| `git diff --check` | PASS | No whitespace errors after packet proof files were written. |
| `python -m json.tool out/rte-pkt-04-prescan-influence/RTE-PKT-04_MANIFEST.json >/tmp/rte-pkt-04-manifest.json` | PASS | Manifest JSON parses. |
| `pre-commit run --files <changed files and packet proof files>` | PASS | Configured hooks passed or skipped for the changed file set. |

## Provider Boundary

No live extraction command was run. No provider preflight was run. No provider batch submit, poll, retrieve, or cancel command was run.

The no-provider safety test monkeypatches `run_extraction_v5.call_llm` to raise if called while exercising compression influence labeling. The test passes, so influence labeling does not require provider calls.

## Known Warning

Existing pytest configuration emits `PytestConfigWarning: Unknown config option: asyncio_mode`. This warning was already present in the RTE-PKT-03 proof and is not changed by this packet.
