# RTE-PKT-07 Regression Triage Closeout

Generated: 2026-05-15T12:56:16Z

## Command Under Triage

```bash
pytest services/repo-truth-extractor/tests/test_llm_runtime_seam.py services/repo-truth-extractor/tests/test_comparison_lane.py services/repo-truth-extractor/tests/test_structured_output_provider_modes.py services/repo-truth-extractor/tests/test_provider_payload_redaction.py services/repo-truth-extractor/tests/test_output_safety.py services/repo-truth-extractor/tests/test_run_extraction_v5_live_readiness.py -q
```

## Implementation Worktree Result

- Worktree: `/Users/hue/.codex/worktrees/39a6/dopemux-mvp`
- Branch: `codex/rte-pkt-07-xai-metadata`
- HEAD before commit: `0179b17b03cf46518aa324bd8f50c805b627631d`
- Result: FAIL, exit code 1.
- Failed test: `services/repo-truth-extractor/tests/test_run_extraction_v5_live_readiness.py::test_route_readiness_summary_honors_benchmark_owned_lane`
- Assertion: expected provider set `{"openai"}`, observed `{"gemini", "openai", "xai"}`.

## Clean Base Result

- Worktree: `/Users/hue/.codex/worktrees/rte-pkt-07-base-0179b17`
- Base SHA: `0179b17b03cf46518aa324bd8f50c805b627631d`
- Checkout state: detached clean base.
- Result: FAIL, exit code 1.
- Failed test: `services/repo-truth-extractor/tests/test_run_extraction_v5_live_readiness.py::test_route_readiness_summary_honors_benchmark_owned_lane`
- Assertion: expected provider set `{"openai"}`, observed `{"gemini", "openai", "xai"}`.

## Classification

`BASELINE_FAILURE`

The implementation and clean base fail the same command, same test, and same provider-set assertion. This does not prove route-readiness correctness; it proves the expanded adjacent failure is not introduced by the RTE-PKT-07 metadata changes.

## Acceptance Impact

The baseline route-readiness failure should remain recorded as unresolved drift, but it does not block committing the RTE-PKT-07 metadata implementation and proof artifacts under the closeout packet rules.

No route-readiness logic, benchmark-owned route behavior, or test expectations were changed.
