# TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001 implementation notes

## Status

`A4_EARLY_REVIEW_REPAIR_IN_PROGRESS`

Implementation authority resumed under amendments
`TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A1` and
`TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A2`, then expanded under
`TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A3`. Early review repair was
authorized under `TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A4`. Merge,
permanent workflow re-enable, credential mutation, final audit, content freeze,
Copilot review before Codex settlement, and metered model spend remain
unauthorized.

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
- Retained automatic non-model CI in `ci-complete.yml` while requiring explicit
  manual dispatch, default-false `allow_api_spend`, and a nonempty Anthropic key
  before its Claude security action can run.
- Converted `security-review.yml` to manual dispatch only with the same
  three-part spend guard.
- Added structural A3 contracts in `tests/ci/test_ai_spend_containment.py` and
  documented that the dispatch input never substitutes for operator authority.

## A4 early-review repair

Local Codex review against PR head `b0be8994658da7f92a7849d21906fd3cafeb693f`
classified one `VALID_IN_SCOPE` defect before external Codex review completion:
repository `embedded-audit.yml` could reach the PAL/Claude provider route from
manual dispatch after review settlement without a default-false
`allow_api_spend` input.

Repair:

- Added `allow_api_spend` to repository `embedded-audit.yml` as optional boolean
  defaulting to `false`, with the same separate-operator-authority language used
  by the other Claude workflows.
- Kept setup/install behind exact head verification and explicit
  `inputs.allow_api_spend == true`.
- Kept the runner executable for fail-closed proof emission, but it now writes a
  non-provider error payload and exits through the existing hard enforcement path
  when API spend authority is absent.
- Added structural tests proving the repository final-audit dispatch defaults
  spend to false and provider runner reachability is dominated by the manual
  spend authority gate.

A4 targeted validation:

- `pytest tests/ci/test_embedded_audit_trigger_policy.py tests/ci/test_ai_spend_containment.py -q`:
  PASS, 25 passed.

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

A3 deterministic evidence:

- Test-first RED: 10 expected failures and 1 pre-existing passing assertion.
- A3 structural GREEN: PASS, 11 passed.
- Embedded-audit authority tests: PASS, 61 passed.
- Executable settlement fixtures: PASS, 5 passed and 7 deselected.
- Complete `tests/ci`: `PASS_WITH_INHERITED_BASELINE_FAILURE`, 64 passed and
  only the exact A2-adjudicated failure.
- Workflow YAML/static parse: PASS, 6 workflow files.
- Task Packet canonical schema: PASS.
- Effective parent+A1+A3 changed-contract and allowlist: PASS, `max_lane=L3`,
  14 paths.
- Live census: embedded audit and both Gemini automatic callers remain
  `disabled_manually`; no feature-branch push model route exists.
- Exact changed-file pre-commit: PASS, all applicable hooks.
- Staged gitleaks scan with redaction: PASS, no leaks found.
- Committed-range, staged, and working-tree `git diff --check`: PASS.

Before commit, `origin/main` advanced from the A2 baseline to
`5900c27d3c38b515204bd5dc4baed8b5e14e2a8e`. The intervening DCP commit changes
no hotfix path. Overlap is empty; no rebase or content refresh was performed.

## Adjudication and bootstrap boundary

Amendment A2 classifies the single inherited failure as non-blocking after the
clean-base reproduction above. `tests/ci/test_pr_gate.py` and
its stale 12-vs-13 assertion remain out of scope and unchanged.

A3 authorizes feature-branch push only after final local gates. Draft PR
creation requires immediate prior disable and live readback of exactly
`embedded-audit.yml`, `security-review.yml`, and `ci-complete.yml`.

## Remaining work

- changed-file pre-commit, staged secret scan, and final diff checks
- commit A3 successor and push feature branch
- temporarily disable exactly three authorized workflows and verify states
- open draft PR
- Codex/Copilot review
- independent final audit and proof finality
