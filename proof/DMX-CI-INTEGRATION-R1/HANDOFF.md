# CI policy and five-path integration disclosure

Content head: `39617b3891fc15c74278aafeb1a31ff5c324a86c`; base main: `583720375df69fbe50f7b8a6b199eaf026f46fb5`. The 56-file manifest is in `review_bundle/SOURCE_MANIFEST.json`.

This candidate integrates the prior completion, memory correction, FastMCP transport and canonical ownership repairs with current main. Five overlapping paths retain current workspace binding and runner-principal semantics. Two inherited memory fixtures were synchronized to the current authentication contract. Four workflows prevent automatic API-backed model calls on PR lifecycle events. Existing explicit comment commands, issue/scheduled triage and non-PR model routes remain outside this task and can still use API credentials.

## Validation and retained failures

- PASS: 598 contained integration tests (306 PM, 13 workflow, 67 memory, 212 identity); 306 CI policy tests; 148 additional worker regressions. Counts describe separate selected groups, not the full suite. Configured precommit, schema, source identity and whitespace checks passed.
- FAIL retained: `tests/ci/test_pr_gate.py::TestCiSummaryStructure::test_ci_summary_needs_exact_job_count` expects 12 jobs while unchanged current main has 13. The same failure was reproduced on the sealed main preimage. The worker's combined run is 454 PASS / 1 FAIL.
- FAIL retained: supplemental Ruff F scan has four findings reproduced on current main: F541 redundant f-string in `services/task-orchestrator/app/main.py`; F401 unused `base64` in `services/working-memory-assistant/chronicle/store.py`; F841 unused `exc` in `src/dopemux/pm/reads.py`; F401 unused `Iterable` in `src/dopemux/workflow/service.py`. The aggregate PRECOMMIT receipt therefore remains FAIL even though configured hooks passed.
- NOT_RUN: full repository suite, hosted CI for this candidate, live integration/concurrency/performance, signed PR-head acceptance, merge and activation.

## Independent review and scope

The fresh Claude source review returned NEEDS_SUPERVISOR. C1-C4 passed static review; C5 is UNKNOWN because the original packet lacked a disclosure document for retained failures and draft-only authority. That original verdict remains unchanged in AUDITOR_REPORT.md. This supervisor-authored document supplied the missing disclosure. A separately authorized, memory-captured C5 review returned PASS_WITH_RISKS; see AUDITOR_REPAIR_REPORT.md. The original NEEDS_SUPERVISOR verdict remains unchanged, and C1-C4 retain their original static scope.

Three LOW findings remain OPEN: the PR Steward evidence-reuse statement was not verifiable from the supplied packet; the CI summary can say to fix required checks even when its deterministic PR Gate is CLEAR; and the pre-existing scheduled-triage concurrency group allows a PR validation run to cancel a scheduled run. No medium/high/critical defect was reported. This was a scoped static review of new policy and integration changes, not comprehensive re-audit of all inherited source or runtime acceptance.

The CLI receipt observes `claude-sonnet-5-5`, requested effort medium. Actual effort is UNKNOWN because the runtime does not echo it. The raw report's self-description of agent SDK/low effort is not execution-identity evidence. One response was observed; the native terminal budget guard exits 1 after that response as previously qualified. No retries or paid fallback were used.

## Authority and release limits

The owner authorized CI policy, five-path integration and a draft PR only. No ready promotion, merge, activation, live-service changes, credential/settings changes or branch-protection changes are authorized. The recorded publication plan requires an acceptable final review. The original publication hold was C5 UNKNOWN, and its two-call allowance remains spent. An intervening disclosure attempt was truncated after ENOSPC and remains closed without a valid verdict. A new owner-authorized, memory-captured C5 review passed with risks, satisfying the condition for draft publication. No source change or signed acceptance is implied. This package is prepared before branch push and draft creation; subsequent publication receipts identify the actual PR/head.

The authorized PR must remain a draft. Required Security Review must report NOT_RUN/pending and stay blocking; it must not turn green merely because its API action was skipped. Trusted embedded-audit and PR Steward gates remain intact. No signed acceptance is claimed. This proof package is unsigned and is not a substitute for those gates.

## Risk and rollback

Risk is high (L3): CI admission and identity-sensitive integration. Preserve both old checkouts, their dirty changes, prior receipts, source preimages and the new isolated branch. Before any merge, rollback consists of closing the draft and retaining evidence; no runtime rollback is necessary because no service was changed. Any later revert/activation requires its own authority. Do not reset, delete or force-push.

## Supplemental review receipt

The fresh response used the existing Max route, observed claude-sonnet-5-5, requested medium/observed effort UNKNOWN, and exactly one response. It used 13,092 input and 2,671 output tokens within 24,000/3,000 and five minutes. No retry, paid fallback, tools or children. Raw reports remain intact. C5 residual risks include author-reported test results, unsigned proof metadata not examined by that disclosure reviewer, and hosted CI still pending. Schema, source identity and proof metadata are checked deterministically by the supervisor; these checks do not grant signed acceptance.
