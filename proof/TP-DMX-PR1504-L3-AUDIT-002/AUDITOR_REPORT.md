# Auditor report — TP-DMX-PR1504-L3-AUDIT-002

Governing auditor: OpenCode CLI 1.18.30, model `kimi-k3`, provider `cheaper-inference`, variant `default`. Session `ses_e405bd5e8ffeFuW9nIk35Ot8Sr`. Operator instruction: "kimi".

- Audited head: `1476638d5f55407a070894d096102771bf15e8bf`
- Base: `f16e0da2cce256096efeaacb1ade625c466dfb6c`
- PR: https://github.com/DDD-Enterprises/dopemux-mvp/pull/1504
- Diff sha256: `5542cbf8d58c6d7c7720c234011ebc91fefbf86cf7aed3ef4b36382bdea52802`
- OpenCode exit: 0
- KIMI_AUDIT.txt sha256: `2c48eb451bf9c3c4d62a98c040ce817d8711fa30a3873ba7696f226c95860d74`
- Signed status: PASS_WITH_RISKS
- Findings: four LOW, accepted as residual risk

## Governing report

## Merge-queue carry-forward audit (PR 1504, head 1476638d)

**Scope:** seven-file diff only, focused on the carry-forward contract: no readiness inheritance without both gates, newest-only branch naming with grouped PRs, per-parent gating, refusal of refs naming non-parents, highest-check-run-id selection, and null-timestamp queued reruns.

**Checks performed:**
- `evaluate()` refuses when the audit check or steward status is missing or not exactly 'success' for every discovered merge parent (tests: missing steward, missing audit).
- First-parent walk collects all non-first parents across chained queue merges; ref naming only the newest PR is accepted while every discovered parent is still gated (test: group with PRs 1440+1466).
- Refs naming a PR outside the discovered parents raise CarryForwardError (test: pr-9999 refused).
- `_check_run_order` sorts by (check-run id, timestamp) with id primary; the highest-id run governs, and a newer queued run with null timestamps yields conclusion None → refusal (test: id 11 queued overrides id 10 success).
- Workflow is fail-closed: script errors or missing payload publish a failure status and fail the job; queue commits cannot satisfy `_open_pr_number`, so a queue commit can never be laundered as a PR parent.

**Verdict:** All six contract clauses are implemented with matching tests. Findings are four low-severity items (dead step output, single-page status read, 10-page check-run cap, carry-time TOCTOU). No medium or higher findings → PASS_WITH_RISKS, conditioned on branch protection requiring the two contexts and on trusted-only producers of those check/status names.

## Findings recorded from the auditor

- CF-1 (low) at .github/workflows/merge-queue-carry-forward.yml (Carry forward step): The step output 'carry_exit' is captured but never consumed; refusal enforcement relies solely on the payload file. Behavior is still fail-closed (missing/!ok payload publishes failure and fails the job), so this is dead code, not a hole.
- CF-2 (low) at scripts/ci/merge_queue_carry_forward.py, GhApi.status_state: status_state reads a single page of the combined-status endpoint with no pagination, unlike check_conclusion which paginates. Worst case is a false refusal (fail-closed) if the context's latest status falls beyond the first page; it cannot produce a false carry because statuses are returned newest-first.
- CF-3 (low) at scripts/ci/merge_queue_carry_forward.py, GhApi.check_conclusion: Check-run collection stops after 10 pages (1000 runs). If API ordering were not newest-first and >1000 same-name runs existed on one sha, the true highest-id run could be missed and an older success treated as newest. Theoretical only; also the API default filter=latest already returns the newest run per name/app.
- CF-4 (low) at scripts/ci/merge_queue_carry_forward.py, evaluate / workflow timing: TOCTOU window: gates on immutable PR-head shas are evaluated at carry time; a rerun completing with failure on the same sha after the queue job succeeded would not retroactively revoke the already-published queue-commit success. Window is small and requires an unusual same-sha rerun.

## Remaining risks from the governing auditor

- Enforcement depends on branch protection / merge-queue rules (outside this diff) actually requiring the 'independent embedded audit' check and 'PR Steward / final readiness' status on queue commits; the workflow only publishes them.
- Gate authenticity depends on only trusted apps/workflows being able to create check runs named 'independent embedded audit' or statuses named 'PR Steward / final readiness' on PR heads; name-based trust is inherited from the existing Grok/AGY producers, not established here.
- If GitHub changes the gh-readonly-queue ref format, parse_queue_pr_numbers returns None and the name-vs-parent refusal check is skipped (all parents are still individually gated, so this degrades safely).
- ci-complete.yml now skips installer-smoke, scoped-coverage, and integration on merge_group; ci-summary's treatment of skipped advisory jobs is only visible via the updated comment, so queue-time coverage of those jobs is assumed, not verified.
