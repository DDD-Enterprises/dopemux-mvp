# RTE-PKT-07 Test Report

Generated: 2026-05-15T10:34:49Z

| Command | Result | Notes |
| --- | --- | --- |
| `python -m py_compile services/repo-truth-extractor/llm_runtime.py services/repo-truth-extractor/run_extraction_v5.py` | PASS | Exit 0. |
| `pytest services/repo-truth-extractor/tests/test_rte_pkt_07_xai_metadata.py -q` | PASS | 8 tests passed. Pytest warned about unknown `asyncio_mode` config. |
| `pytest services/repo-truth-extractor/tests/test_llm_runtime_seam.py services/repo-truth-extractor/tests/test_comparison_lane.py services/repo-truth-extractor/tests/test_structured_output_provider_modes.py services/repo-truth-extractor/tests/test_provider_payload_redaction.py services/repo-truth-extractor/tests/test_output_safety.py -q` | PASS | 30 adjacent seam, comparison, structured-output, and redaction tests passed. Pytest warned about unknown `asyncio_mode` config. |
| `pytest services/repo-truth-extractor/tests/test_llm_runtime_seam.py services/repo-truth-extractor/tests/test_comparison_lane.py services/repo-truth-extractor/tests/test_structured_output_provider_modes.py services/repo-truth-extractor/tests/test_provider_payload_redaction.py services/repo-truth-extractor/tests/test_output_safety.py services/repo-truth-extractor/tests/test_run_extraction_v5_live_readiness.py -q` | FAIL | One unrelated route-readiness assertion failed: `test_route_readiness_summary_honors_benchmark_owned_lane` expected only `openai`, observed `gemini`, `openai`, and `xai`. No edited metadata path was implicated. |
| `pytest services/repo-truth-extractor/tests -k 'xai and metadata' -q` | PASS | 8 selected tests passed. |
| `pytest services/repo-truth-extractor/tests -k 'provider and metadata' -q` | PASS | 4 selected tests passed. |
| `pytest services/repo-truth-extractor/tests -k 'llm_runtime or response_summary' -q` | PASS | 5 selected tests passed. |
| `pytest services/repo-truth-extractor/tests/test_artifact_provenance_fields.py services/repo-truth-extractor/tests/test_truth_label_preservation.py -q` | PASS | 11 provenance/truth-label tests passed. Pytest warned about unknown `asyncio_mode` config. |

## Closeout Regression Triage

| Worktree | Command | Result | Notes |
| --- | --- | --- | --- |
| Implementation `/Users/hue/.codex/worktrees/39a6/dopemux-mvp` | `pytest services/repo-truth-extractor/tests/test_llm_runtime_seam.py services/repo-truth-extractor/tests/test_comparison_lane.py services/repo-truth-extractor/tests/test_structured_output_provider_modes.py services/repo-truth-extractor/tests/test_provider_payload_redaction.py services/repo-truth-extractor/tests/test_output_safety.py services/repo-truth-extractor/tests/test_run_extraction_v5_live_readiness.py -q` | FAIL exit 1 | Same failure as parent report: `test_route_readiness_summary_honors_benchmark_owned_lane` expected `openai`, observed `gemini`, `openai`, `xai`. |
| Clean base `/Users/hue/.codex/worktrees/rte-pkt-07-base-0179b17` at `0179b17b03cf46518aa324bd8f50c805b627631d` | Same command | FAIL exit 1 | Same failing test and same observed provider set. Classification: `BASELINE_FAILURE`. |

Acceptance impact: the expanded adjacent live-readiness route failure is baseline/stale relative to the RTE-PKT-07 dirty implementation and does not indicate a new metadata regression.

## Final Closeout Validation

| Command | Result | Notes |
| --- | --- | --- |
| `python -m py_compile services/repo-truth-extractor/llm_runtime.py services/repo-truth-extractor/run_extraction_v5.py` | PASS | Exit 0 after closeout proof update. |
| `pytest services/repo-truth-extractor/tests/test_rte_pkt_07_xai_metadata.py -q` | PASS | 8 tests passed. Pytest warned about unknown `asyncio_mode` config. |
| `pytest services/repo-truth-extractor/tests -k 'xai and metadata' -q` | PASS | 8 selected tests passed. Pytest warned about unknown `asyncio_mode` config. |
| `pytest services/repo-truth-extractor/tests -k 'provider and metadata' -q` | PASS | 4 selected tests passed. Pytest warned about unknown `asyncio_mode` config. |
| `pytest services/repo-truth-extractor/tests -k 'llm_runtime or response_summary' -q` | PASS | 5 selected tests passed. Pytest warned about unknown `asyncio_mode` config. |
| `pytest services/repo-truth-extractor/tests/test_artifact_provenance_fields.py services/repo-truth-extractor/tests/test_truth_label_preservation.py -q` | PASS | 11 tests passed. Pytest warned about unknown `asyncio_mode` config. |
| `python -m json.tool out/rte-pkt-07-xai-metadata/RTE-PKT-07_MANIFEST.json >/dev/null` | PASS | Exit 0. |
| `git diff --check` | PASS | Exit 0. |
| `git status --short --branch` | PASS | Dirty only before commit: allowed parent implementation files, new metadata test, and proof output root. |

No live/provider/batch validation command was run.
