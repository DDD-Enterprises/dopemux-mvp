# A2 inherited baseline failure reproduction

## Authority

`TP-DMX-EMBEDDED-AUDIT-COST-CONTAINMENT-001-A2`

## Clean base

- path: `/private/tmp/dopemux-pr-review-frontload-s0`
- checkout: detached
- head: `c7bc2fb479d7386825df73e028acdce723ee3388`
- status before test: clean
- command: `uv run --frozen pytest tests/ci -q`
- environment: CPython 3.12.13, locked `uv.lock`, task-scoped uv cache

## Comparison

| Surface | Clean base | Hotfix working tree |
|---|---|---|
| failing test | `TestCiSummaryStructure.test_ci_summary_needs_exact_job_count` | same |
| assertion | `13 == (7 + 5)` | same |
| result | 1 failed, 41 passed | 1 failed, 53 passed |

Hotfix adds 12 tests in `tests/ci/test_embedded_audit_trigger_policy.py`; no
additional failure appears.

## Byte identity

| Path | working blob | `origin/main` blob |
|---|---|---|
| `tests/ci/test_pr_gate.py` | `3467595777a5d2fa74b3fd20f7c6e396b60efe30` | `3467595777a5d2fa74b3fd20f7c6e396b60efe30` |
| `.github/workflows/ci-complete.yml` | `d148691ae4436fa32157f129d2f1b9887563957c` | `d148691ae4436fa32157f129d2f1b9887563957c` |

`git diff --exit-code origin/main -- tests/ci/test_pr_gate.py
.github/workflows/ci-complete.yml` exited 0.

## Classification

`PASS_WITH_INHERITED_BASELINE_FAILURE`

Failure is pre-existing stale test expectation. It is not caused by the
embedded-audit cost-containment hotfix. No edit authority exists for either
adjudicated path under this packet.
