---
id: pr-steward-solo-maintainer-org-app
title: Solo-maintainer org app security-release approval
type: runbook
owner: '@hu3mann'
last_review: 2026-07-26
next_review: 2026-10-24
author: '@hu3mann'
date: '2026-07-26'
prelude: Solo-maintainer org app security-release approval (runbook) for dopemux
  documentation and developer workflows.
---

# Solo-maintainer org-app security-release approval

## Policy

`SOLO_MAINTAINER_ORG_APP_APPROVAL` (TP-PRSTEWARD-SOLO-MAINTAINER-ORG-APP-001).

Red-lane security-release approval accepts **either**:

1. An exact-head `APPROVED` review from a trusted **human** who is **not** the
   PR author; or
2. An exact-head `APPROVED` review from a **specifically trusted** organization-
   owned GitHub App registered in `trusted_security_release_apps`.

The app route does **not** waive independent audit, CI, proof freshness, or
deployment gates. Approval never overrides other steward blockers.

## Config

`tools/pr_steward/known_reviewers.json`:

```json
{
  "trusted_security_release_approvers": ["hu3mann"],
  "trusted_security_release_apps": [
    {
      "login": "ddd-release-gate[bot]",
      "owner": "DDD-Enterprises",
      "installation_scope": "DDD-Enterprises/dopemux-mvp"
    }
  ]
}
```

Generic `github-actions[bot]` / Dependabot are never accepted as release apps.

## One-time operator bootstrap (GitHub App)

1. Create a GitHub App owned by **DDD-Enterprises** named e.g. `ddd-release-gate`.
2. Permissions (minimum useful set):
   - Metadata: read
   - Contents: read
   - Actions: read
   - Checks: read
   - Pull requests: **write** (create reviews only)
3. Install **only** on `DDD-Enterprises/dopemux-mvp`.
4. Do **not** grant contents write, admin, secrets, deployments, or workflow write.
5. Any automation that posts the app review must load from trusted `main`, not
   PR-controlled code.

## Using the app on a red-lane PR

After required CI is green and independent audit is `PASS` / `PASS_WITH_RISKS`
at the exact head:

1. Confirm head OID has not moved.
2. App submits `APPROVE` review bound to that commit OID.
3. Re-run PR Steward.
4. Require `MERGE_READINESS.status = READY` before merge.
5. Deployment remains a separate operator decision.

## Bootstrap authorization (recorded)

This policy exists only to replace an unsatisfiable second-human requirement for
a solo-maintainer org repository. It does not approve any specific product PR
(including dope-context repair PRs) and does not waive implementation, audit,
CI, proof, or deployment gates.
