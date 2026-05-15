# RTE-PKT-01 Test Report

Generated: `2026-05-15T02:18:28.825840+00:00`

No provider credentials were required. No test intentionally submitted, polled, retrieved, or cancelled provider jobs. Live-capable functions in the new terminality tests were monkeypatched to fail if invoked without consent.

| Command | Result | Details |
|---|---|---|
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py -q` | `PASS` | 26 passed; warning: unknown pytest config option asyncio_mode. |
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py::test_cli_help_mentions_execute_live_ok_and_list_phases services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py::test_cli_live_execution_requires_explicit_consent -q` | `PASS` | 41 passed; warning: unknown pytest config option asyncio_mode. |
| `env -u DPMX_LIVE_OK python services/repo-truth-extractor/run_extraction_v5.py --phase A --run-id rte_pkt_01_cli_no_consent` | `PASS_EXPECTED_REFUSAL` | Exited 2 with explicit refusal before provider/network dispatch; message listed missing --execute and DPMX_LIVE_OK=1. |
| `env -u DPMX_LIVE_OK python services/repo-truth-extractor/run_extraction_v5.py --batch-retrieve --batch-ids batch_123 --dry-run` | `PASS_EXPECTED_REFUSAL` | Exited 2 with explicit refusal before batch retrieval dispatch; message listed missing DPMX_LIVE_OK=1. |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py` | `PASS` | Exit 0. |
| `git diff --check` | `PASS` | Exit 0 before proof artifact generation; rerun after proof generation is required. |
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py -q` | `FAIL_EXISTING_OUT_OF_SCOPE` | Exit 1. Unrelated failure in test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback: escalation_trigger observed provider_failure, expected None. |
| `pytest services/repo-truth-extractor/tests -k 'live_gate or consent or pre_live or batch_watch or batch_retrieve or online_prescan' -q` | `FAIL_EXISTING_OUT_OF_SCOPE` | Exit 1. Selector includes test_pre_live_gate_v25.py::test_default_policy_requires_direct_gemini_and_xai; DEFAULT_TARGET_POLICY observed cost, expected balanced_openrouter. |

## Regression Triage Closeout

| Command | Result | Details |
|---|---|---|
| `pwd; git rev-parse --show-toplevel; git branch --show-current || true; git rev-parse HEAD; git status --short --branch; git diff --name-only` | `PASS` | exit 0; Captured implementation branch state before triage. |
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py::test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback -q` | `FAIL_BASELINE_COMPARISON_IMPL` | exit 1; Implementation branch failure: escalation_trigger observed provider_failure, expected None. |
| `pytest services/repo-truth-extractor/tests/test_pre_live_gate_v25.py::test_default_policy_requires_direct_gemini_and_xai -q` | `FAIL_BASELINE_COMPARISON_IMPL` | exit 1; Implementation branch failure: DEFAULT_TARGET_POLICY observed cost, expected balanced_openrouter. |
| `git worktree add --detach /Users/hue/.codex/worktrees/rte-pkt-01-base-triage a4214ca5bf431e1b59791661e2b664a6cd24c1da` | `PASS` | exit 0; Created clean detached base comparison worktree. |
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py::test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback -q (base worktree)` | `FAIL_BASELINE` | exit 1; Clean base failure: same escalation_trigger provider_failure vs None assertion. |
| `pytest services/repo-truth-extractor/tests/test_pre_live_gate_v25.py::test_default_policy_requires_direct_gemini_and_xai -q (base worktree)` | `FAIL_BASELINE` | exit 1; Clean base failure: same DEFAULT_TARGET_POLICY cost vs balanced_openrouter assertion. |
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py -q` | `PASS` | exit 0; 26 passed; warning: unknown pytest config option asyncio_mode. |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py` | `PASS` | exit 0; No syntax errors. |
| `git diff --check` | `PASS` | exit 0; No whitespace errors. |
| `git status --short --branch` | `PASS` | exit 0; Dirty state is limited to allowed runtime/test/proof outputs. |

## Final Closeout Validation

| Command | Exit | Result | Detail |
|---|---:|---|---|
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py -q` | 0 | `PASS` | 26 passed; warning: unknown pytest config option asyncio_mode. |
| `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_live_gate_terminality.py services/repo-truth-extractor/tests/test_run_extraction_v5_validator.py services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py::test_cli_help_mentions_execute_live_ok_and_list_phases services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py::test_cli_live_execution_requires_explicit_consent -q` | 0 | `PASS` | 41 passed; warning: unknown pytest config option asyncio_mode. |
| `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py` | 0 | `PASS` | No syntax errors. |
| `git diff --check` | 0 | `PASS` | No whitespace errors in tracked diff at closeout validation. |
| `git status --short --branch` | 0 | `PASS` | Dirty state before staging is limited to allowed runtime/test/proof paths. |
