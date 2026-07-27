---
id: TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001
project: dopemux-mvp
target: tools/pr_steward/solo_owner_security_release.py
series: pr-steward
risk: HIGH
status: implementing
parent_policy: ADR-DMX-PRSTEWARD-SOLOOWNER-001
parent_pr: 1131
related_product_pr: 1126
title: Tp Prsteward Solo Owner Org Member 001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Tp Prsteward Solo Owner Org Member 001 (explanation) for dopemux documentation
  and developer workflows.
---
# TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001

## Objective

Repair PR Steward solo-owner security-release policy so the sole trusted
maintainer of an organization-owned repository may authorize an exact-head
red-lane PR when GitHub reports their repository association as `MEMBER`.

Preserve every other security, proof, audit, review, CI, exact-head, and
multi-approver gate.

## Root cause

`tools/pr_steward/solo_owner_security_release.py` defined:

```python
_OWNER_ASSOCIATIONS = frozenset({"OWNER"})
```

For organization-owned repositories, human org maintainers are reported as
`MEMBER`, so legitimate exact-head solo-owner authorization was rejected early.

## Required policy

Solo-operator associations: exactly `{OWNER, MEMBER}`.

- `OWNER` — user-owned repositories
- `MEMBER` — organization-owned repositories
- `COLLABORATOR` and all other values do not activate
- Association acceptance never replaces exact single-person trusted roster
- Non-author trusted security approver disables solo-owner route
- Authorization comment must be authored by PR author and sole trusted approver
- Comment must match exact PR number and full 40-char head SHA
- Audit, proof, CI, review-thread, reviewer-classification, harvest, mixed-SHA
  gates remain independently blocking
- Auto-merge remains disabled
- Solo-owner receipt never becomes a fabricated GitHub review
- When both PR and comment associations are present and differ →
  `SOLO_OWNER_ASSOCIATION_MISMATCH`

## Scope IN

- `tools/pr_steward/solo_owner_security_release.py`
- `tests/pr_steward/test_solo_owner_security_release.py`
- `tests/pr_steward/test_classifier_solo_owner.py`
- `docs/90-adr/adr-dmx-prsteward-soloowner-001.md`
- `task-packets/pr-steward/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001.md`
- `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/**`

## Scope OUT

- `known_reviewers.json`, ordinary security-release approval/app paths
- schemas, `.github/**`, services/dope-context/**
- PR #1126 branch, PR #1133 policy, red-lane classifications
- opportunistic cleanup

## Stop conditions

Stop if allowlist escape, COLLABORATOR accepted, roster condition weakened,
multi-reviewer enforcement changes, app approval semantics change, non-security
blocker waived, tests fail, independent audit FAIL/NEEDS_SUPERVISOR, secrets
appear, or PR #1126 modified before this policy lands.
