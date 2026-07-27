---
id: adr-dmx-prsteward-org-app-001
title: 'PR Steward Org-Owned GitHub App Security-Release Approval'
type: adr
owner: '@hu3mann'
author: 'Grok Build, for operator decision'
date: '2026-07-27'
last_review: '2026-07-27'
next_review: '2026-10-25'
status: accepted
prelude: Allow a dedicated DDD-Enterprises-owned GitHub App to satisfy security-release approval after exact-head audit and CI, without inventing a second human reviewer.
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-dmx-prsteward-soloowner-001
---

# ADR-DMX-PRSTEWARD-ORG-APP-001: Org-Owned Release-Gate App Approval

**Status:** Accepted
**Policy name:** `SOLO_MAINTAINER_ORG_APP_APPROVAL`
**Packet:** `TP-PRSTEWARD-SOLO-MAINTAINER-ORG-APP-001`

## Context

A GitHub organization cannot sign in, author a PR review, or approve a PR. Actions are attributed to a user or app identity.

GitHub Apps may create pull-request reviews when granted `Pull requests: write`.

The prior solo-owner phrase path remains valid but is operator-manual. An organization-owned release-gate app is a more explicit automated authority for a solo-maintainer repository:

- one human operator;
- one deterministic automated release gate;
- distinction is explicit and testable.

Inventing a second personal account controlled by the same human is rejected as false independence.

## Decision

PR Steward security-release approval accepts **either**:

1. Exact-head `APPROVED` review from a trusted human who is not required to be distinct when using other paths, with association OWNER/MEMBER/COLLABORATOR; **or**
2. Exact-head `APPROVED` review from a login listed in `trusted_security_release_apps`, with app-suitable association (typically `NONE`), never generic `github-actions[bot]`.

### App path preconditions

The app approval counts only when all hold:

- exact repository, PR number, and full head SHA binding;
- independent audit `PASS` or non-blocking `PASS_WITH_RISKS`;
- required CI green at that head;
- current proof matching that head;
- no unresolved blocking review threads;
- no unknown/unclassified review items that already form blockers;
- app listed with owner `DDD-Enterprises` and installation_scope covering the repo;
- dedicated app identity (not `github-actions[bot]` / dependabot).

App approvals **never** waive non-security blockers. They only satisfy `SECURITY_RELEASE_*`.

### Operational requirements (outside code)

- App owned/installed by `DDD-Enterprises`, installed only on target repo(s).
- Workflow or app logic that posts reviews must load from trusted main (or external app service), not untrusted PR code.
- Permissions minimal: Metadata read, Contents read, Actions read, Checks read, Pull requests write. No secrets, admin, deployments, or workflow write.

### Config shape

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

## Relationship to solo-owner phrase path

Solo-owner phrase override (ADR-DMX-PRSTEWARD-SOLOOWNER-001) remains available. Preferred automated path for ongoing solo maintenance is the org app once installed and posting exact-head reviews.

## Non-goals

- Approving implementation quality via the app alone;
- Auto-merge;
- Deployment authorization;
- Fake second-human accounts.

## Rollback

Revert this ADR’s implementation commits; remove `trusted_security_release_apps`; re-run PR Steward tests.
