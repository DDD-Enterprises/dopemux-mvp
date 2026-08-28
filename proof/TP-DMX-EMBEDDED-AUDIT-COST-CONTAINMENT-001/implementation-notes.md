# TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001 implementation notes

## Status

`LOCAL_GATES_COMPLETE_READY_TO_COMMIT`

Implementation authority resumed under amendments
`TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A1` and
`TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A2`. Merge, workflow re-enable,
and metered model spend remain unauthorized.

## Implemented working-tree slice

- Removed automatic PR triggers from repository and init-template
  `embedded-audit.yml` workflows.
- Retained required manual PR number/head SHA inputs and trusted-source/head
  integrity controls.
- Added bounded review-settlement GraphQL preflight before checkout, auditor
  routing, setup, installation, or invocation.
- Added repository and init-template readiness invalidators that write only
  pending commit status for `PR Steward / final readiness`.
- Updated trigger and PR-gate runbooks.
- Updated A1-authorized audit workflow tests and added executable preflight
  fixtures plus structural policy tests.

## Validation evidence

- `pytest tests/audit/test_run_embedded_audit.py -q`: PASS, 61 passed.
- Executable settlement-gate fixtures: PASS, 5 passed.
- Focused trigger-policy set: PASS, 9 passed before executable fixtures were
  added.
- `pytest tests/ci -q`: FAIL, 1 failed and 53 passed.
  `TestCiSummaryStructure.test_ci_summary_needs_exact_job_count` expects 12
  `ci-summary.needs` entries while unchanged `origin/main` workflow has 13.
  Both `.github/workflows/ci-complete.yml` and
  `tests/ci/test_pr_gate.py` are unchanged from `origin/main`; failure is not
  caused by embedded-audit trigger changes.

A2 clean-base reproduction at
`/private/tmp/dopemux-pr-review-frontload-s0`, detached exact head
`c7bc2fb479d7386825df73e028acdce723ee3388`:

- same command and locked uv environment
- same exact failing test
- same `13 == (7 + 5)` assertion
- base result: 1 failed, 41 passed
- hotfix result: 1 failed, 53 passed (12 added hotfix policy tests)
- adjudicated file blob identities match `origin/main`

Detailed evidence:
`review_bundle/A2_BASELINE_REPRODUCTION.md`.

Remaining local gates:

- workflow syntax/YAML validation: PASS, 4 files
- Task Packet canonical schema: PASS
- changed-contract: PASS, `max_lane=L3`, 10 paths
- formal parent+A1 changed-file allowlist: PASS, 10 paths
- `git diff --check` and staged diff check: PASS
- staged gitleaks scan with redaction: PASS, no leaks found
- changed-file pre-commit: PASS, all applicable hooks
- final relevant audit/init tests: PASS, 138 passed
- final `tests/ci`: `PASS_WITH_INHERITED_BASELINE_FAILURE`, 53 passed and
  the exact A2-adjudicated failure only

Before commit, `origin/main` advanced from the A2 baseline to
`5900c27d3c38b515204bd5dc4baed8b5e14e2a8e`. The intervening DCP commit changes
no hotfix path. Overlap is empty; no rebase or content refresh was performed.

## Blocker

Amendment A2 classifies the single inherited failure as non-blocking after the
clean-base reproduction above. `tests/ci/test_pr_gate.py` and
`.github/workflows/ci-complete.yml` remain out of scope and unchanged.

## Remaining work

- commit
- trusted-main automatic-spend census before push
- push and draft PR only if census permits
- Codex/Copilot review
- independent final audit and proof finality
