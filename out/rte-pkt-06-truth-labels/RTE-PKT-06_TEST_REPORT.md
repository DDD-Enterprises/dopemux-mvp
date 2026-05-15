# RTE-PKT-06 Test Report

All validation was local. No provider credentials were required.

| Command | Result | Notes |
| --- | --- | --- |
| `python -m py_compile services/repo-truth-extractor/lib/truth_labels.py services/repo-truth-extractor/lib/artifact_provenance.py services/repo-truth-extractor/run_extraction_v5.py` | PASS | Early syntax check before tests. |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/lib/artifact_provenance.py services/repo-truth-extractor/lib/truth_labels.py services/repo-truth-extractor/tests/test_truth_label_preservation.py` | PASS | Runtime, helper, and new tests compile. |
| `pytest services/repo-truth-extractor/tests/test_truth_label_preservation.py -q` | PASS | 6 passed. |
| `pytest services/repo-truth-extractor/tests -k 'truth and labels' -q` | PASS | 1 selected test passed. |
| `pytest services/repo-truth-extractor/tests -k 'unknown or conflicting' -q` | PASS | 20 selected tests passed. |
| `pytest services/repo-truth-extractor/tests/test_artifact_provenance_fields.py -q` | PASS | 5 passed; RTE-PKT-05 provenance regression. |
| `pytest services/repo-truth-extractor/tests -k 'provenance and repair' -q` | PASS | 12 selected tests passed. |
| `pytest services/repo-truth-extractor/tests -k 'sidefill and provenance' -q` | PASS | 1 selected test passed. |
| `pytest services/repo-truth-extractor/tests -k 'repair or sidefill' -q` | PASS | 28 selected tests passed. |
| `pytest services/repo-truth-extractor/tests/test_comparison_summary.py services/repo-truth-extractor/tests/test_comparison_lane.py -q` | PASS | 13 passed; comparison lane regression. |
| `pytest services/repo-truth-extractor/tests/test_failed_sidecar_redaction.py -q` | PASS | 5 passed; redaction regression. |
| `git diff --check` | PASS | No whitespace or patch hygiene errors. |
| `pre-commit run --files ...` | PASS | Changed-file hooks passed. |

Warning observed in pytest runs: `PytestConfigWarning: Unknown config option: asyncio_mode`. This warning existed in local pytest configuration behavior and did not fail the targeted runs.

Post-proof git status is recorded in the final response.
