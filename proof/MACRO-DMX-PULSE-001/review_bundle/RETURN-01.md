# MACRO-DMX-PULSE-001 - Aggregate Return 01

**Status**: `READY_FOR_AUDIT` is NOT claimed. The final audit returned `PASS_WITH_RISKS` (Grok), with Q3 = FAIL (F1). Hand-off state: `NEEDS_SUPERVISOR` on one operator decision (accept or repair F1).
**Authority**: NONE. This aggregate mints no PASS/READY/DONE. Nothing pushed, signed, merged or opened as a PR.
**Authorization consumed**: operator message `AUTHORIZE_MACRO_DMX_PULSE_001_EXECUTION=YES` (2026-10-21); "In the repo" placement; the Grok audit approval (2026-10-22).

## Custody
Worktree `/Users/hue/code/dopemux-mvp/.worktrees/pulse-001`, branch `feat/pulse-001`, base `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`. Coordinator was the sole committer; children did not commit. Frozen head `1d2219e8c894c5929ceba6ac5f2650dfe7ba2147`.

## Children
| WS | Commit | Files | TP_ROUTE requested | Observed (transcript `message.model`) | Advisor | Status |
|---|---|---|---|---|---|---|
| W01 engine /state aliases | `3dbced397` | 2 | claude-sonnet-5-5 | claude-sonnet-5-5 | 0 | PASS (own re-run) |
| W02 dopemux-pulse mod | `2e27c6fe3` | 5 | claude-sonnet-5-5 | claude-sonnet-5-5 | 0 | PASS after supervisor rulings |
| W03 how-to | `1d2219e8c` | 1 | claude-haiku-5-5 | claude-haiku-5-5 | 0 | PASS |
Effort: not settable through the Agent tool; observed UNKNOWN.

## Supervisor rulings
- R1: the command is `/pulse-focus`, not `/focus` (Claude Code ships `/focus` and refuses to register it). The packet text was corrected.
- R2: the mod survives `/clear` (`session.end` with `reason: 'clear'` keeps timers).

## Gates run by the coordinator
`test_state_contract.py` 4 pass; `tests/arch` 184 pass; `claude plugin validate` pass (2 non-blocking warnings); `claude plugin test` 24/24; `tsc` clean; black/flake8 clean on the new Python file, `routes.py` flake8 339 = 339; `git diff --check`; `validate_change_contract` L2 PASS; pre-commit range PASS.
F5 baseline (re-run for this bundle): `services/adhd_engine/tests` on base = 28 failed, 88 passed, 4 errors; on head = 28 failed, 92 passed, 4 errors; failing IDs identical (`F5_BASE_RUN.txt`, `F5_HEAD_RUN.txt`).

## Audit
agy attempt failed (429): `AGY_ATTEMPT_RECORD.md`. Grok audit: `GROK_RUN_RECORD.md`, `GROK_AUDIT_RESPONSE.txt`, `GROK_ADJUDICATION.md`. Raw streams were lost (see EVIDENCE LOST).

## Next material blocker
Operator: accept F1 (orphaned fetch after the 2 s race) as a residual risk, or authorize a small repair (hold `isPolling` until the fetch settles, plus the README `/done` wording) and a fresh audit on a newly approved route.
