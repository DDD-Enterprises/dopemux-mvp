---
id: PCP-PR-STEWARD
title: Generic PCP PR Steward (Advisory)
type: reference
owner: '@hu3mann'
date: '2026-06-23'
author: '@hu3mann'
last_review: '2026-06-26'
next_review: '2026-09-24'
prelude: Generic PCP PR Steward (Advisory) (explanation) for dopemux documentation
  and developer workflows.
---
# Generic PCP PR Steward

`dopemux.pcp.pr_steward` harvests PR evidence read-only and emits a `MERGE_READINESS` signal.

## Advisory-only

- `advisory` is always `true`.
- Output is **not** merge authority and never invokes merge/push/commit commands.
- Green CI is **not** semantic proof.

## Fail-closed READY

`READY` is withheld when any blocking condition is present, including:

- `INCOMPLETE_INTAKE` when any `intake_completeness` category is not `COMPLETE`
- `STALE_PROOF` when proof is missing/stale/unknown
- `FAILED_CHECK` / `STALE_CHECK`
- `UNKNOWN_REVIEWER_OR_BOT` / `UNCLASSIFIED_REVIEW_ITEM`
- `UNRESOLVED_BLOCKING_THREAD`
- `DIFF_OUTSIDE_ALLOWLIST`
- `MISSING_SECURITY_RELEASE_APPROVAL`

## Intake completeness

`harvest_pr_intake` marks categories it cannot fully harvest as `MISSING` or `UNKNOWN` (for example `proof_refs`, `review_comments`, `issue_comments`). Such harvests cannot produce `READY` without a specialized downstream enricher.

Schema validates field presence, not the truthfulness of audit/approval/allowlist claims.
