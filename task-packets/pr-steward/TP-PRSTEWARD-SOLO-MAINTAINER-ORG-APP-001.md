---
id: tp-prsteward-solo-maintainer-org-app-001
title: TP-PRSTEWARD-SOLO-MAINTAINER-ORG-APP-001
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-27'
last_review: '2026-07-27'
next_review: '2026-10-25'
prelude: Bootstrap packet for org-owned GitHub App security-release approvals.
---

# TP-PRSTEWARD-SOLO-MAINTAINER-ORG-APP-001

## Mission

Replace the impossible second-human security-release requirement for a solo-maintainer repo with an explicit organization-owned GitHub App authority.

## Bootstrap authorization (operator)

```text
BOOTSTRAP_AUTHORIZATION:
Modify PR Steward so an organization-owned GitHub App may satisfy
security-release approval after exact-head independent audit and CI verification.

This authorization does not approve PR #1126.
It does not waive any implementation, audit, CI, proof, or deployment gate.
It exists only to replace an impossible second-human requirement with an
explicit automated release authority suitable for a solo-maintainer repository.
```

## Disposition

```text
PR_1126=HOLD
MERGE=FORBIDDEN
DEPLOY=FORBIDDEN
NEXT_ACTION=BOOTSTRAP_ORG_OWNED_RELEASE_GATE_APP_POLICY
```

## Implementation

- `tools/pr_steward/security_release_approval.py` — human + app evaluators
- `tools/pr_steward/classifier.py` — app gate re-eval after proof/audit
- `tools/pr_steward/known_reviewers.json` — `trusted_security_release_apps`
- tests + ADR + runbook

## Operator follow-up after policy merge

1. Create/install `ddd-release-gate` app (see runbook).
2. Have app approve PR #1126 at head `ba8a78fa1ed09dc0d7cbb9f2b2680508c6fa13a3` only when audit/CI/proof green.
3. Re-run PR Steward until READY.
4. Separate merge authorization for #1126.
5. Deployment remains a separate operator decision.
