# RTE-PKT-15 Test Report

## PASS

- `pytest services/repo-truth-extractor/tests/test_failed_sidecar_redaction.py -q`
  - Result: PASS, 5 passed.
  - Warning: `PytestConfigWarning` for unknown `asyncio_mode`.
- `pytest services/repo-truth-extractor/tests/test_output_safety.py -q`
  - Result: PASS, 6 passed.
  - Warning: `PytestConfigWarning` for unknown `asyncio_mode`.
- `pytest services/repo-truth-extractor/tests -k 'failed and redaction' -q`
  - Result: PASS, 5 passed.
  - Warning: `PytestConfigWarning` for unknown `asyncio_mode`.
- `python -m py_compile services/repo-truth-extractor/run_extraction_v5.py services/repo-truth-extractor/output_safety.py services/repo-truth-extractor/tests/test_failed_sidecar_redaction.py`
  - Result: PASS, exit code 0.
- `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_concurrency.py -q`
  - Result: PASS, 2 passed.
  - Warning: `PytestConfigWarning` for unknown `asyncio_mode`.
- `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py::test_classify_request_failure_distinguishes_batch_terminal_and_parse_failures -q`
  - Result: PASS, 1 passed.
  - Warning: `PytestConfigWarning` for unknown `asyncio_mode`.
- `git diff --check`
  - Result: PASS, exit code 0.
- `pre-commit run --files ...`
  - Result: PASS, exit code 0.
  - Observed: docs/location/root-hygiene hooks passed or skipped where no files applied.
- `python -m json.tool out/rte-pkt-15-failed-sidecars/RTE-PKT-15_MANIFEST.json >/dev/null`
  - Result: PASS, exit code 0.
- `python -c 'from pathlib import Path; pats=["RTE"+"PKT15","s"+"k-","A"*4,"B"*4,"C"*4,"PRIVATE "+"KEY-----","Bearer "+"X"]; text="\n".join(p.read_text(encoding="utf-8") for p in Path("out/rte-pkt-15-failed-sidecars").glob("**/*") if p.is_file()); hits=[p for p in pats if p in text]; raise SystemExit(1 if hits else 0)'`
  - Result: PASS, no matches.

## FAIL

- `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py services/repo-truth-extractor/tests/test_run_extraction_v5_concurrency.py -q`
  - Result: FAIL, 1 failed and 23 passed.
  - Failing assertion: `test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback` expected `request_meta["escalation_trigger"] is None`; observed `provider_failure`.
  - Scope assessment: the changed lines do not modify provider-failure escalation semantics. This packet did not broaden into that failure.

## REGRESSION TRIAGE

- Implementation branch command:
  - `pytest services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py services/repo-truth-extractor/tests/test_run_extraction_v5_concurrency.py -q`
  - Result: FAIL, 1 failed and 23 passed.
  - Failing test: `test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback`.
  - Observed value: `provider_failure`.
- Clean base worktree:
  - Path: `/Users/hue/.codex/worktrees/rte-pkt-15a-clean-base`
  - SHA: `a4214ca5bf431e1b59791661e2b664a6cd24c1da`
  - Result: FAIL, 1 failed and 23 passed.
  - Failing test: `test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback`.
  - Observed value: `provider_failure`.
- Classification: `BASELINE_FAILURE`.
- Acceptance impact: not a new regression from RTE-PKT-15 sidecar redaction.

## NOT_RUN

- `pytest services/repo-truth-extractor/tests/test_provider_payload_redaction.py -q`
  - Reason: file is not present in this checkout.
- Live/provider/batch network validation.
  - Reason: forbidden by packet.

## Provider boundary

No validation command used provider credentials, submitted provider batch jobs, polled provider batch jobs, retrieved provider batch jobs, cancelled provider batch jobs, or ran live extraction.
