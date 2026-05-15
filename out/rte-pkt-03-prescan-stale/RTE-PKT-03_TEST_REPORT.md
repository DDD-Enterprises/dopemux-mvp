# RTE-PKT-03 Test Report

| Command | Result | Notes |
| --- | --- | --- |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/lib/intelligence_router.py services/repo-truth-extractor/lib/prescan/engine.py` | PASS | Exit 0. |
| `pytest services/repo-truth-extractor/tests/test_prescan_import_staleness.py services/repo-truth-extractor/tests/test_prescan_v5_integration.py -q` | PASS | 13 passed. Pytest warned about unknown config option `asyncio_mode`. |
| `pytest services/repo-truth-extractor/tests -k 'prescan and stale' -q` | PASS | 8 passed. Pytest warned about unknown config option `asyncio_mode`. |
| `pytest services/repo-truth-extractor/tests -k 'prescan and import' -q` | FAIL | Selector included out-of-scope `test_code_prescan_truthfulness.py::test_code_prescan_emits_dotted_relative_python_imports`; failure was `KeyError: 'imports'`. |
| `pytest services/repo-truth-extractor/tests -k 'prescan and default_excludes' -q` | PASS | 1 passed. Pytest warned about unknown config option `asyncio_mode`. |
| `pytest services/repo-truth-extractor/tests/test_code_prescan_truthfulness.py::test_code_prescan_emits_dotted_relative_python_imports -q` | FAIL | Reproduced the out-of-scope selector failure directly. |
| `python -m json.tool out/rte-pkt-03-prescan-stale/RTE-PKT-03_MANIFEST.json` | PASS | Manifest parses as JSON. |
| `git diff --check` | PASS | Exit 0. |
| `pre-commit run --files <changed files>` | PASS | Configured hooks passed or skipped for the changed file set. |

No live extraction was run. No provider credentials were required.
