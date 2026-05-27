---
id: pr-fixtures
title: Pr Fixtures
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-27'
last_review: '2026-05-27'
next_review: '2026-08-25'
prelude: Pr Fixtures (explanation) for dopemux documentation and developer workflows.
---
# PR Steward and Action Bridge Fixtures

**TP**: TP-DMX-PR-FIXTURES-011
**Series**: DMX-EMBEDDED-AUDIT-PR-CLEANUP-RECONCILED

Offline deterministic fixtures for testing the PR Steward intake pipeline and the
Action Bridge compiler. No live GitHub calls. No network dependency.

---

## PR Steward Fixtures (`tests/fixtures/pr_steward/`)

Each subdirectory contains a `harvest.json` consumed by
`tools.pr_steward.intake --fixture-dir`. Intake exits 0 for READY and 2 for
any non-READY readiness state.

### Green (exit 0)

| Fixture | Readiness | Notes |
|---|---|---|
| `ready_all_green` | READY | All checks pass, fresh proof, known author |
| `ready_with_resolved_outdated_threads` | READY | Outdated threads marked AUTO_APPLIED (non-blocking) |

### Blocking (exit 2)

| Fixture | Readiness | Primary Blocker |
|---|---|---|
| `draft_pr_blocks` | BLOCKED | `PR_IS_DRAFT` |
| `missing_auth_or_harvest_blocks` | BLOCKED | `HARVEST_INCOMPLETE` |
| `failed_check_blocks` | NEEDS_IMPLEMENTER | `FAILED_CHECK` |
| `unresolved_thread_blocks` | NEEDS_IMPLEMENTER | `UNRESOLVED_REVIEW_THREAD` |
| `pending_check_not_ready` | NOT_READY | `PENDING_CHECK` |
| `mixed_sha_checks_block` | NEEDS_SUPERVISOR | `MIXED_SHA_ARTIFACT_SET` |
| `skipped_required_audit_blocks` | NEEDS_SUPERVISOR | `EMBEDDED_AUDIT_SKIPPED` |
| `unknown_reviewer_blocks` | NEEDS_SUPERVISOR | `UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION` |
| `proof_stale_blocks` | NEEDS_SUPERVISOR | `PROOF_STALE` — proof bundle SHA does not match PR head |
| `proof_missing_blocks` | NEEDS_SUPERVISOR | `PROOF_MISSING` — proof field is empty |
| `unknown_pr_author_blocks` | NEEDS_SUPERVISOR | `UNKNOWN_PR_AUTHOR` — author not in `known_reviewers.json` and no trusted `authorAssociation` |

### Proof Blocker Detail

| Blocker | `proof` shape in harvest | Cause |
|---|---|---|
| `PROOF_STALE` | `{"proof_path": "...", "proof_head_sha": "<old>", "matches_pr_head": false}` | Proof exists but was produced at a different commit |
| `PROOF_MISSING` | `{}` (empty object) | No proof bundle present |

Both map to readiness `NEEDS_SUPERVISOR` and risk tier `HIGH`.

### UNKNOWN_PR_AUTHOR Detail

The `unknown_pr_author_blocks` fixture has `pr.author.login = "external-bot"`,
which is not in `known_reviewers.json` and carries no `authorAssociation` in the
OWNER / MEMBER / COLLABORATOR trusted set.

An author is trusted if **any** of the following hold:
1. `pr.author.login` is in `known_reviewers.json#known_reviewers`
2. `pr.authorAssociation` is in `known_reviewers.json#trusted_author_associations`
3. `pr.author.authorAssociation` (nested GraphQL shape) is in the trusted set

---

## Action Bridge Fixtures (`tests/fixtures/pr_action_bridge/`)

Each file is a JSON object with four keys matching the inputs to
`tools.pr_action_bridge.compiler.compile_action_plan`:

```json
{
  "merge_readiness": { ... },
  "review_ledger":   { ... },
  "thread_dispositions": { ... },
  "ci_triage":       { ... }
}
```

| Fixture | Readiness | Expected Category | Target Role |
|---|---|---|---|
| `ready_green.json` | READY | — (no actions) | — |
| `needs_supervisor_proof_stale.json` | NEEDS_SUPERVISOR | `proof-stale` | supervisor |
| `needs_supervisor_proof_missing.json` | NEEDS_SUPERVISOR | `proof-missing` | supervisor |
| `needs_supervisor_unknown_author.json` | NEEDS_SUPERVISOR | `unknown-pr-author` | supervisor |
| `needs_implementer_failed_check.json` | NEEDS_IMPLEMENTER | `failed-check` | implementer |

### Action category → rationale

| Category | Rationale (abbreviated) |
|---|---|
| `proof-stale` | Proof bundle is stale; supervisor must re-run proof/audit at current head SHA. |
| `proof-missing` | Proof bundle is missing; supervisor must produce proof/audit bundle before proceeding. |
| `unknown-pr-author` | PR author is not in known_reviewers.json; supervisor must verify author before proceeding. |
| `failed-check` | CI check failed; implementer must investigate and fix. |

---

## Test Coverage

| Test file | What it covers |
|---|---|
| `tests/pr_steward/test_intake.py` — `test_blocking_fixtures_fail_closed` | All 10 blocking fixtures (including 3 new ones) |
| `tests/pr_action_bridge/test_compiler_fixtures.py` | All 5 Action Bridge fixtures, schema validation, rationale content |
