---
id: pr-gate-runbook
title: Pr Gate Runbook
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-27'
last_review: '2026-05-27'
next_review: '2026-08-25'
prelude: Pr Gate Runbook (explanation) for dopemux documentation and developer workflows.
---
# PR Gate Runbook

> **Status**: Active — `ci-summary` job in `.github/workflows/ci-complete.yml`
> exits 1 when required checks fail, making it a hard gate for PRs.

---

## Overview

The `ci-summary` job is the single convergence point for all upstream CI jobs.
It runs with `if: always()` (executes even when upstream jobs fail) and
unconditionally produces a GitHub Step Summary with ADHD-friendly status.

At the end of that step, a gate section evaluates the **required blocking jobs**
and exits 1 if any of them did not succeed. Because `ci-summary` itself exits 1,
GitHub marks it as failed — which branch protection can use as a required check.

---

## Job Classification Matrix

| Job | Classification | Reason |
|---|---|---|
| `code-quality` | **REQUIRED BLOCKING** | Always runs on PRs; linting / type-check regressions must block merge |
| `tests` | **REQUIRED BLOCKING** | Always runs on PRs; unit-test regressions must block merge |
| `extractor-smoke` | **REQUIRED BLOCKING** | Always runs on PRs; focused canonical RTE regression gate |
| `extractor-full` | **ADVISORY** | Uses `set +e; exit 0` trap — job `result` is structurally always `success`; informational display only via `outputs.suite_status` |
| `installer-smoke` | **ADVISORY** | `if: github.event_name != 'pull_request'` — skipped on all PR runs |
| `scoped-coverage` | **ADVISORY** | `if: github.event_name != 'pull_request'` — skipped on all PR runs |
| `integration` | **ADVISORY** | `if: github.event_name != 'pull_request'` — skipped on all PR runs |
| `security` | **ADVISORY** | May be skipped when API keys are absent; non-blocking by design |
| `docs` | **ADVISORY** | Documentation link checks; non-blocking |

---

## Gate Logic (ci-complete.yml)

```bash
_gate_ok=true
[ "${{ needs.code-quality.result }}"    != "success" ] && _gate_ok=false
[ "${{ needs.tests.result }}"           != "success" ] && _gate_ok=false
[ "${{ needs.extractor-smoke.result }}" != "success" ] && _gate_ok=false
if [ "$_gate_ok" = "false" ]; then
  # posts "PR Gate: BLOCKED" to step summary, then:
  exit 1
fi
# posts "PR Gate: CLEAR" to step summary
```

The gate uses `!= "success"` (not `== "failure"`) so that `skipped` and
`cancelled` states also block the gate. This prevents advisory-lane skip
conditions from accidentally clearing a required check.

---

## Branch Protection Configuration

> ⚠️ **UNKNOWN** — Branch protection truth cannot be verified from inside the
> worktree. An operator must manually confirm the following.

**Required operator action**: verify that `ci-summary` (display name
`"📊 CI Pipeline Summary"`) is listed as a **required status check** in the
branch protection rule for `main`.

Steps (GitHub UI):
1. Repository → Settings → Branches → Branch protection rules → `main`
2. Check "Require status checks to pass before merging"
3. Search for `ci-summary` or `📊 CI Pipeline Summary` in the required checks list
4. If absent: add it, save

Until this is confirmed, the gate logic is structurally correct but not enforced
at the GitHub branch-protection layer.

---

## Failure Response Procedures

### Required check failed (code-quality / tests / extractor-smoke)

1. Identify which check failed from the Step Summary (`PR Gate: BLOCKED` line
   includes the result of each required job).
2. Navigate to the failing job's log.
3. Fix the regression; push a new commit to the PR branch.
4. Required checks re-run automatically on the new push.

### Advisory check failed (extractor-full / installer-smoke / scoped-coverage / integration / security / docs)

Advisory failures are **non-blocking** for merge. They appear in the Step
Summary but do not cause `ci-summary` to exit 1.

Recommended response:
- `extractor-full` advisory failure: file a follow-up issue; mark tests as
  expected-failure or fix on a separate branch.
- Skipped advisory jobs: expected on PR fast-path; no action needed.

### ci-summary itself fails unexpectedly

If `ci-summary` fails for a reason other than the gate (e.g., runner error),
re-run it via GitHub Actions → Re-run jobs → Re-run failed jobs.

---

## Structural Tests

Gate invariants are enforced by `tests/ci/test_pr_gate.py`:

```bash
python -m pytest tests/ci/ -v
```

Tests assert:
- `ci-summary` has `if: always()`
- All 9 upstream jobs present in `needs`
- Gate script uses `!= "success"` for each required blocking job
- `exit 1` present in gate script
- `extractor-full.result` does not feed into `exit 1`
- `UNKNOWN` caveat documented in gate script
- `advisory` carve-out documented in gate script
- `PR Gate: BLOCKED` and `PR Gate: CLEAR` messages present
- No trailing whitespace in gate script
