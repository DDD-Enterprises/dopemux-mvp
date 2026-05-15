# RTE-PKT-05 Test Report

All commands below were local. No provider credentials were required.

| Command | Result | Notes |
| --- | --- | --- |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/lib/artifact_provenance.py` | PASS | Exit 0 |
| `pytest services/repo-truth-extractor/tests/test_artifact_provenance_fields.py -q` | PASS | 5 passed |
| `pytest services/repo-truth-extractor/tests/test_phase_d_sidefill.py services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py -q` | PASS | 11 passed |
| `pytest services/repo-truth-extractor/tests/test_comparison_summary.py services/repo-truth-extractor/tests/test_comparison_lane.py -q` | PASS | 13 passed |
| `pytest services/repo-truth-extractor/tests -k 'provenance and repair' -q` | PASS | 12 passed |
| `pytest services/repo-truth-extractor/tests -k 'sidefill and provenance' -q` | PASS | 1 passed |
| `pytest services/repo-truth-extractor/tests/test_failed_sidecar_redaction.py -q` | PASS | 5 passed |
| `pytest services/repo-truth-extractor/tests -k 'repair or sidefill' -q` | PASS | 24 passed |
| `python -m json.tool out/rte-pkt-05-provenance-fields/RTE-PKT-05_MANIFEST.json >/dev/null` | PASS | Exit 0 |
| `git diff --check` | PASS | Exit 0 |
| `pre-commit run --files <changed files>` | PASS | Exit 0 |
| forbidden-root change scan with `rg` | PASS | Exit 1, expected no-match result |

Common warning:

`PytestConfigWarning: Unknown config option: asyncio_mode`

The warning is pre-existing test configuration behavior observed during these targeted runs.
