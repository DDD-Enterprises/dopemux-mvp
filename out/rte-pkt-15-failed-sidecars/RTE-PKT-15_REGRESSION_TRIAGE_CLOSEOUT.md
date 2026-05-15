# RTE-PKT-15 Regression Triage Closeout

## REG-001 command

`pytest services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py services/repo-truth-extractor/tests/test_run_extraction_v5_concurrency.py -q`

## Implementation branch result

- Worktree: `/Users/hue/.codex/worktrees/a8da/dopemux-mvp`
- Branch: `codex/rte-pkt-15-failed-sidecars`
- HEAD: `a4214ca5bf431e1b59791661e2b664a6cd24c1da`
- Result: FAIL
- Summary: 1 failed, 23 passed.
- Failing test: `test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback`
- Assertion: expected `payload["request_meta"]["escalation_trigger"] is None`
- Observed value: `provider_failure`

## Clean base result

- Worktree: `/Users/hue/.codex/worktrees/rte-pkt-15a-clean-base`
- Branch: detached HEAD
- HEAD: `a4214ca5bf431e1b59791661e2b664a6cd24c1da`
- Result: FAIL
- Summary: 1 failed, 23 passed.
- Failing test: `test_current_partition_execution_preserves_provider_failure_semantics_before_parse_fallback`
- Assertion: expected `payload["request_meta"]["escalation_trigger"] is None`
- Observed value: `provider_failure`

## Classification

`BASELINE_FAILURE`

The implementation branch and clean base fail the same command on the same test with the same assertion and observed value. The line number differs because the implementation branch adds sidecar-redaction code above the logged runtime line, but the tested behavior and assertion are identical.

## Acceptance impact

This failure does not block committing RTE-PKT-15 closeout under the packet policy because it is proven baseline behavior, not a new regression from failed-sidecar redaction.

The failure remains outside this packet's implementation scope. No provider escalation semantics or broader prelive hardening test expectations were changed.
