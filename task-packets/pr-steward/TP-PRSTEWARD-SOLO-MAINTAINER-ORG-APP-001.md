---
id: TP-PRSTEWARD-SOLO-MAINTAINER-ORG-APP-001
title: Solo-maintainer org-app security-release approval bootstrap
type: explanation
owner: '@hu3mann'
last_review: 2026-07-26
next_review: 2026-10-24
author: '@hu3mann'
date: '2026-07-26'
prelude: Solo-maintainer org-app security-release approval bootstrap (explanation)
  for dopemux documentation and developer workflows.
---

# TP-PRSTEWARD-SOLO-MAINTAINER-ORG-APP-001

## BOOTSTRAP_AUTHORIZATION

Modify PR Steward so an organization-owned GitHub App may satisfy
security-release approval after exact-head independent audit and CI verification.

This authorization does **not** approve PR #1126.
It does **not** waive any implementation, audit, CI, proof, or deployment gate.
It exists only to replace an impossible second-human requirement with an
explicit automated release authority suitable for a solo-maintainer repository.

## Objective

Allow red-lane PRs to be approved by either:

1. a trusted human who is not the author; or
2. a dedicated `DDD-Enterprises` GitHub App (`ddd-release-gate[bot]`) at exact head.

## Scope IN

- `tools/pr_steward/known_reviewers.json`
- `tools/pr_steward/security_release_approval.py`
- `tools/pr_steward/classifier.py`
- `tests/pr_steward/test_trusted_security_approvers.py`
- `tests/pr_steward/test_classifier_security_release_gate.py`
- `tests/pr_steward/test_security_release_approval.py`
- `docs/ops/pr-steward-solo-maintainer-org-app.md`
- this task packet

## Scope OUT

- PR #1126 branch / dope-context product code
- red-lane path definitions
- self-approval for human authors
- generic `github-actions[bot]` as approver
- deployment automation

## Acceptance

- `hu3mann` remains a trusted human approver (cannot self-approve own PRs).
- `ddd-release-gate[bot]` is recognized when configured scope matches the repo.
- Untrusted reviewers cannot satisfy the gate.
- Ordinary bots cannot satisfy the gate.
- Red-lane path classification unchanged.
- Tests pass.
