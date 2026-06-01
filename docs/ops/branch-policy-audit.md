---
id: branch-policy-audit
title: Branch Policy Audit
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-27'
last_review: '2026-05-31'
next_review: '2026-08-25'
prelude: Branch Policy Audit (explanation) for dopemux documentation and developer
  workflows.
---
# Branch Protection Policy Audit

> **Status**: Evidence refreshed 2026-05-31 via read-only `gh api`.
> **Executor**: Codex (read-only; no mutations performed).

---

## Summary

Two overlapping protection layers govern the `main` branch:

1. **Classic branch protection** — `/branches/main/protection`
2. **Ruleset 13063360** — "Default branch protection (restored after history rewrite)"

Both are active. The ruleset does not override the classic protection;
they are additive.

---

## Classic Branch Protection (`/branches/main/protection`)

### Required Status Checks

`strict: true` — branch must be up to date with base before merging.

| Check Context | App |
|---|---|
| `🔒 Security Review` | GitHub Actions (15368) |
| `📚 Documentation Check` | GitHub Actions (15368) |
| `identity-check` | GitHub Actions (15368) |
| `🧪 Unit Tests` | GitHub Actions (15368) |
| `Analyze (python)` | GitHub Actions (15368) |
| `Analyze (javascript-typescript)` | GitHub Actions (15368) |
| `Analyze (ruby)` | GitHub Actions (15368) |
| `📊 CI Pipeline Summary` | GitHub Actions (15368) |

`📊 CI Pipeline Summary` is the GitHub status context for the
`.github/workflows/ci-complete.yml` `ci-summary` job.

### Other Settings

| Setting | Value |
|---|---|
| Required approving reviews | 0 |
| Dismiss stale reviews | false |
| Require code owner review | false |
| Require last push approval | false |
| Enforce admins | **false** — admins bypass |
| Required linear history | **true** — squash/rebase only |
| Allow force pushes | false |
| Allow deletions | false |
| Required conversation resolution | true |
| Block creations | false |

---

## Ruleset 13063360 — Default Branch Protection

**Name**: "Default branch protection (restored after history rewrite)"
**Scope**: `~DEFAULT_BRANCH` (main)
**Enforcement**: active
**Created**: 2026-02-20 | **Updated**: 2026-04-21

### Rules

| Rule Type | Parameters |
|---|---|
| `deletion` | Prevents branch deletion |
| `non_fast_forward` | Prevents force-push |
| `pull_request` | 0 approvals, thread resolution required, squash+rebase allowed |
| `copilot_code_review` | `review_on_push: false`, `review_draft_pull_requests: false` |

**No required status checks rule in the ruleset.**
The 7 required checks are enforced exclusively through classic protection.

### Bypass Actors (all bypass mode: `always`)

| Actor Type | Notes |
|---|---|
| OrganizationAdmin | Bypasses all rules |
| DeployKey | Bypasses all rules |
| RepositoryRole 4 (Maintain) | Bypasses all rules |
| RepositoryRole 5 (Admin) | Bypasses all rules |

---

## Gap Analysis

| Item | Status | Action Required |
|---|---|---|
| `ci-summary` in required checks | PASS — `📊 CI Pipeline Summary` present | None |
| Force push protection | PASS — both classic + ruleset prevent it | None |
| Deletion protection | PASS — both layers | None |
| Required conversation resolution | PASS | None |
| Squash/rebase enforced | PASS — linear history required | None |
| Copilot cloud-agent review | OFF — `review_on_push: false` | Correct; Copilot cloud-agent enablement is red-lane supervisor item |
| Admin bypass | ALWAYS — `enforce_admins: false`, bypass actors | Accepted operational posture; document in risk register |
| 0 approvals required | Active | Acceptable if required checks + thread resolution compensate |

---

## Required Operator Action

No branch-protection mutation is required for `ci-summary` as of the
2026-05-31 read-only refresh. Re-run the evidence commands below after any
GitHub settings change or required-check rename.

---

## Raw Evidence Provenance

Captured via:
```bash
gh api repos/DDD-Enterprises/dopemux-mvp/branches/main/protection
gh api repos/DDD-Enterprises/dopemux-mvp/rulesets
gh api repos/DDD-Enterprises/dopemux-mvp/rulesets/13063360
```

Timestamp: 2026-05-27. Re-run to refresh.

Refreshed via the same read-only API calls on 2026-05-31. The refresh observed
`📊 CI Pipeline Summary` in classic branch protection's
`required_status_checks.contexts` and observed ruleset `13063360` still active
with deletion, non-fast-forward, pull-request, and Copilot-code-review rules.
