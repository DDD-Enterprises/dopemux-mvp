---
id: ops-pr-acceptance
title: DevOps AutoPR PR Acceptance
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: PR acceptance gates for embedded audit, PR Steward readiness, and second-supervisor skip decisions.
---
# DevOps AutoPR PR Acceptance

## Acceptance Gates

A PR is eligible for normal closeout only when all of these are true:

- repo identity, branch, base branch, and head SHA are recorded
- task packet is schema-valid or manual schema gap is explicitly recorded
- changed files are within the packet allowlist
- proof is current to the PR head SHA
- `proof/<PACKET_ID>/review_bundle/` exists as the single upload/review unit
- embedded audit is `PASS` or non-blocking `PASS_WITH_RISKS`
- PR Steward check-only intake is `READY`
- every review item, issue comment, review comment, review thread, and CI check is classified
- no unknown or untrusted reviewer or bot remains unclassified
- no blocking thread, failed required check, stale proof, or unresolved audit finding remains

## Skip-Second-GPT-5.5 Rule

Skip the second GPT-5.5 Pro supervisor review only when both gates are READY:

1. embedded audit is `PASS` or non-blocking `PASS_WITH_RISKS`
2. PR Steward merge readiness is `READY`

If either gate is missing, skipped, stale, failed, or unknown, the PR requires supervisor review or human escalation.

No second GPT-5.5 Pro prompt can be skipped unless PR Steward emits `READY` and embedded audit is `PASS` or nonblocking `PASS_WITH_RISKS`. Unknown or untrusted reviewers and bots and unresolved review threads both block `READY`.

Explicit known reviewer logins are trusted. GitHub `authorAssociation` values `OWNER`, `MEMBER`, and `COLLABORATOR` are trusted unless a future policy overrides this rule. External unknown actors and unclassified bots block `READY`.

## Non-Automation Boundary

This acceptance policy does not implement auto-fix, thread resolution, auto-merge, merge queue mutation, or active GitHub mutation. It defines gate evidence only.
