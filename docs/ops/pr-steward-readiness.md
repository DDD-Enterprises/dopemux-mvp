---
id: pr-steward-readiness
title: Pr Steward Readiness
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-27'
last_review: '2026-05-27'
next_review: '2026-08-25'
prelude: Pr Steward Readiness (explanation) for dopemux documentation and developer
  workflows.
---
# PR Steward Readiness Classification

> **Status**: Updated 2026-05-26 as part of TP-DMX-PR-STEWARD-HARDEN-010.

---

## Readiness Tiers

| Readiness | Risk Tier | Meaning |
|---|---|---|
| `BLOCKED` | `CRITICAL` | Hard blocker — PR cannot be evaluated (draft, closed, harvest incomplete, mixed SHAs) |
| `NEEDS_SUPERVISOR` | `HIGH` | Human supervisor must act before any merge path opens |
| `NEEDS_IMPLEMENTER` | `MEDIUM` | PR author must resolve (failed checks, open threads, review changes) |
| `NOT_READY` | `LOW` | Waiting on CI (pending checks) |
| `READY` | `CLEAR` | All gates pass; proof fresh and matching |

---

## Blocker Registry

### BLOCKED tier

| Blocker | Cause |
|---|---|
| `HARVEST_INCOMPLETE` | `harvest_complete: false` in harvest payload |
| `PR_IS_DRAFT` | PR is marked draft |
| `PR_CLOSED` | PR state is not OPEN and `allow_closed=false` |
| `MIXED_SHA_ARTIFACT_SET` | Check artifacts contain a SHA that does not match `pr.head_sha` |

### NEEDS_SUPERVISOR tier

| Blocker | Cause |
|---|---|
| `UNKNOWN_PR_AUTHOR` | PR author not in `known_reviewers.json` and not a trusted association |
| `PROOF_STALE` | Proof SHA present but does not match current PR head |
| `PROOF_MISSING` | Proof SHA absent (no proof bundle found) |
| `UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION` | Review from author not in known reviewers |
| `UNKNOWN_CHECK` | Required check not in the known-checks registry |
| `REVIEW_ITEM_NEEDS_SUPERVISOR` | Comment contains "needs supervisor" marker |
| `EMBEDDED_AUDIT_*` | Embedded PAL audit status is FAIL, NEEDS_SUPERVISOR, SKIPPED, or unknown |

### NEEDS_IMPLEMENTER tier

| Blocker | Cause |
|---|---|
| `UNRESOLVED_REVIEW_THREAD` | PR has unresolved blocking review thread |
| `FAILED_CHECK` | Required CI check exited failure/cancelled |
| `REQUEST_CHANGES` | Reviewer left REQUEST_CHANGES review |
| `REVIEW_ITEM_MUST_FIX` | Review comment marked P1 or P2 |

### NOT_READY tier

| Blocker | Cause |
|---|---|
| `PENDING_CHECK` | Required CI check still queued / in-progress |

---

## PROOF_STALE vs PROOF_MISSING

Prior to schema 1.1.0 both stale and missing proof emitted a single `PROOF_STALE_OR_MISSING` blocker.
As of TP-DMX-PR-STEWARD-HARDEN-010:

- **`PROOF_STALE`**: Proof exists but `proof_head_sha` does not match the current PR head SHA. The PR was likely updated after the last proof run. Re-run the proof cycle.
- **`PROOF_MISSING`**: No proof bundle found (`proof_head_sha` absent). No proof has been produced for this PR. Run the full TP cycle and produce a proof bundle.

Both remain `NEEDS_SUPERVISOR` tier and map to the `proof-stale` / `proof-missing` action categories in the Action Bridge.

---

## UNKNOWN_PR_AUTHOR

Added in schema 1.1.0. The classifier checks the PR author's login against:

1. `known_reviewers` list in `tools/pr_steward/known_reviewers.json`
2. `trusted_author_associations` (OWNER, MEMBER, COLLABORATOR)

If the author matches neither, `UNKNOWN_PR_AUTHOR` is appended to blockers and an entry is added to unknowns: `"Unknown PR author: <login>"`.

**Operator action**: Review the PR author and either add them to `known_reviewers.json` or proceed with manual supervisor sign-off.

---

## risk_tier Field

Added to `MERGE_READINESS.json` in schema 1.1.0. Derived from `readiness`:

```
BLOCKED          → CRITICAL
NEEDS_SUPERVISOR → HIGH
NEEDS_IMPLEMENTER → MEDIUM
NOT_READY        → LOW
READY            → CLEAR
```

Consumers can use `risk_tier` for dashboards, alerting, or routing without re-deriving from the blocker set.

---

## Schema Version History

| Version | Changes |
|---|---|
| `1.0.0` | Initial schema |
| `1.1.0` | Added `risk_tier` field; split `PROOF_STALE_OR_MISSING` into `PROOF_STALE` / `PROOF_MISSING`; added `UNKNOWN_PR_AUTHOR` blocker |
