You are an independent embedded auditor reviewing a fail-closed security repair before merge. This working tree is a git worktree pinned at the exact commit under audit: 1c59dafd19817d7af7033245d3e1342927c38af5 (branch tp/DMX-RTE-V5-TERMINAL-PROVENANCE-001, on top of PR #1232's frozen content head 492208f4684f1b7660be26deda7c29161ea50070, repo DDD-Enterprises/dopemux-mvp). This commit is the sole substantive repair commit under packet TP-DMX-RTE-V5-P1-FAIL-CLOSED-REPAIR-001; do not trust this framing, re-derive everything from `git show`/`git diff`/the files themselves in this worktree.

## Background (for context only — verify independently, don't just trust this)

PR #1232 was marked ready for review at content head 492208f4. A subsequent review pass (Codex + Copilot) surfaced two P1 findings on that exact head:

1. **RTE-W1-010 (source identity bypass):** in `services/repo-truth-extractor/run_extraction_v5.py`, the fail-closed gate `required_execution_source_identity(root)` sat immediately before `runners = {` inside `main()` — textually *after* `write_run_manifest`/`write_runner_identity`/`write_confidence_ramp_artifacts` and after the `--async-provider`/`--finalize`/`--batch-watch`/`--batch-retrieve` CLI dispatch blocks, each of which calls `sys.exit()` on its own before ever reaching the gate. An UNKNOWN/unproven git source identity therefore never blocked those paths.
2. **RTE-W1-006 V5 terminal (batch outcome laundering):** in `services/repo-truth-extractor/lib/batch_retriever.py` / `run_extraction_v5.py`'s `run_batch_retrieval_and_integration_detailed`, a provider terminal-failure batch (`failed`/`expired`/`cancelled`/`canceled`/`timeout`) whose `batch.failed` webhook event integrated successfully was counted as `integrated`, so `outcome.failed` stayed 0 and the run reached the `fully_integrated` success branch (`exit_code=0`) even though the batch itself failed upstream.

The commit under audit, 1c59dafd19, claims to repair both, scoped to exactly four files:
`services/repo-truth-extractor/run_extraction_v5.py`,
`services/repo-truth-extractor/lib/batch_retriever.py`,
`services/repo-truth-extractor/tests/test_rte_v5_terminal_provenance_fail_closed.py`,
`services/repo-truth-extractor/tests/test_batch_retriever.py`.

## Audit scope — re-derive the control flow yourself, do not just read the commit message

Inspect `git show 1c59dafd19 --stat` and the full diff, then read the actual current source (not just the diff) in `services/repo-truth-extractor/run_extraction_v5.py` and `services/repo-truth-extractor/lib/batch_retriever.py`. Specifically re-derive and test each of these claims against the CURRENT code, tracing actual control flow (not just trusting comments):

1. Source identity (`required_execution_source_identity`) dominates every canonical evidence write (RUN_MANIFEST.json / RUNNER_IDENTITY.json / confidence-ramp artifacts) — trace that every write call in `main()` is textually and control-flow reachable only after the gate call, for every CLI branch that reaches it.
2. Source identity dominates Stage-0 online prescan (`run_integrated_prescan_stage`, reachable when `--prescan-online` or `--allow-online-llm` is set).
3. Source identity dominates async submit (`--async-provider` / `run_phase_R_async_submit`).
4. Source identity dominates finalize (`--finalize` / `run_phase_R_finalize`).
5. Source identity dominates batch watch (`--batch-watch` / `run_batch_watch`).
6. Source identity dominates batch retrieval (`--batch-retrieve` / `run_batch_retrieval_and_integration_detailed`).
7. Normal phase execution (`--phase X`) remains gated — the `runners = {...}` dispatch dict is unreachable without passing the gate.
8. Legitimate read-only/introspection CLI modes (`--print-config`, `--print-run-order`, `--doctor-auth`, `--preflight-providers`, `--print-promptpack`, `--coverage-report`/`--verify-phase-output` with no persist, `--doctor` with persist=False) remain usable and are NOT blocked by an unproven identity — confirm they all textually return/exit before the gate.
9. In `run_batch_retrieval_and_integration_detailed`, confirm a batch whose provider status is `failed`/`expired`/`cancelled`/`canceled`/`timeout` cannot produce `exit_code=0`/`success=True`, even when its webhook integration succeeds cleanly (i.e., a clean `batch.failed` webhook insert cannot launder a provider failure into overall success).
10. Confirm the fix does NOT suppress or skip `integrate_batch_results_with_webhook_detailed`'s webhook-event integration for a failed batch — the event must still be recorded, only the outcome-level success determination changes.
11. Confirm fully-successful terminal batch sets (`completed`/`succeeded`/`done`, no failures) still produce `success=True`/`exit_code=0` — the new check must not regress the happy path.
12. Confirm a nonterminal / zero-terminal-work retrieval (batches still in-progress upstream) still classifies as `no_terminal_batches_yet` / `success=True`, not a failure.
13. Confirm the new `terminal_failure_batches` counter is not double-counted against, or double-subtracted from, the pre-existing `failed`/`unmapped` accounting (i.e., it's an orthogonal signal, not overlapping bookkeeping that could produce a wrong count elsewhere in the proof/telemetry).

## Explicitly disclosed residual concerns — evaluate whether these are real gaps or acceptable

The implementer (a prior Claude Code session) disclosed two specific residual concerns in their own handoff. Assess both directly rather than taking "already disclosed" as license to skip:

A. The new `--async-provider`/`--finalize` end-to-end tests (`test_s10_async_provider_submit_blocked_before_dispatch`, `test_s10_finalize_blocked_before_dispatch` in `tests/test_rte_v5_terminal_provenance_fail_closed.py`) stub the downstream dispatch functions to raise `AssertionError` if called, but the surrounding `main()` code wraps those specific dispatch calls in `except Exception: sys.exit(1)`. An `AssertionError` from the stub would therefore be caught by that `except Exception` and produce the *same* exit code (1) the test expects on a correctly-gated run — meaning those two tests cannot currently distinguish "the gate blocked me" from "the gate was bypassed and my stub's own AssertionError got silently swallowed". Determine whether this is a real test-quality gap (and if so, how a reviewer could actually verify the gate holds for these two paths) or whether the companion structural test (`test_s7_required_execution_source_identity_gate_is_a_single_call_site`, which asserts strict source-order placement of the gate before every write/dispatch marker including these two) sufficiently closes the gap in combination.

B. CLI shapes that previously never reached the identity gate now write a `RUN_MANIFEST.json` startup-failure record (`run_status: "FAILED"`, `failure_reason: "source_identity_unproven"`) via `update_run_manifest_startup_failure` when identity is unproven, whereas before they wrote nothing. Confirm this failure-record shape (a) matches the pre-existing pattern already used elsewhere in this file for other startup failures (e.g. `cost_cap_setup_failed`, `launch_provider_preflight_failed`), and (b) does not itself contain fields that would let a downstream consumer mistake it for evidence of a runnable/completed canonical execution (e.g. it should have no `phases`, no `prompt_set_integrity`, no certification claim).

## Test evidence

Independently run (or re-derive by reading) the new/changed tests in this worktree:
`cd services/repo-truth-extractor && python3 -m pytest tests/test_rte_v5_terminal_provenance_fail_closed.py tests/test_batch_retriever.py -q`
and ideally the full `tests/` directory if time permits. Do not just trust that a prior run passed — actually execute it in this worktree if your sandbox permits, or explain clearly if it does not and what you inspected instead.

## Required output

Return Markdown with:
- verdict: PASS, PASS_WITH_RISKS, FAIL, or NEEDS_SUPERVISOR
- blocking findings (explicit "none" if none)
- non-blocking risks (must explicitly address items A and B above, even if you conclude they're acceptable)
- files reviewed
- validation evidence reviewed (test run output or explicit explanation if you could not execute tests)
- authority-boundary / scope concerns (confirm the diff touches only the four allowed files and nothing in v3/v4, CLI routing, schemas, workflows, or `proof/pr_merge/embedded-audit/pr-1232/**`)
- explicit confirmation or refutation of each of the 13 numbered claims above, one by one

Do not edit any files. Do not merge, push, or commit anything. This is a read-only audit of the exact commit 1c59dafd19817d7af7033245d3e1342927c38af5.
