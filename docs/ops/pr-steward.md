---
id: ops-pr-steward
title: PR Steward V1
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Check-only PR review intake design scaffold for PR Steward v1.
---
# PR Steward V1

## Purpose

PR Steward v1 is a check-only review-intake gate. It does not mutate GitHub, apply fixes, resolve threads, enqueue merges, approve PRs, or merge PRs.

The v1 GitHub Actions workflow is advisory. It may emit `NOT_READY`, `NEEDS_IMPLEMENTER`, `NEEDS_SUPERVISOR`, or `BLOCKED` while other checks are still running, but it does not fail the workflow job for those readiness states and must not be configured as a required branch-protection check until the pending-check race is solved.

## Inputs

PR Steward must harvest:

- PR metadata
- changed files
- commits and head SHA
- reviews
- review comments
- review threads
- issue comments
- status checks and CI state
- current proof bundle and embedded audit status

## Required Outputs

| Output | Schema |
| --- | --- |
| `MERGE_READINESS.json` | `schemas/pr_steward/merge_readiness.schema.json` |
| `REVIEW_ITEM_LEDGER.json` | `schemas/pr_steward/review_item_ledger.schema.json` |
| `THREAD_DISPOSITIONS.json` | `schemas/pr_steward/thread_dispositions.schema.json` |
| `CI_TRIAGE.json` | `schemas/pr_steward/ci_triage.schema.json` |
| `PR_STATE_SNAPSHOT.json` | `schemas/pr_steward/pr_state_snapshot.schema.json` |

## Dispositions

Allowed review item dispositions:

- `AUTO_APPLIED`
- `MUST_FIX`
- `OPTIONAL_DEFERRED`
- `OUT_OF_SCOPE_FOLLOWUP`
- `REJECTED_WITH_REASON`
- `NEEDS_SUPERVISOR`
- `UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION`

`AUTO_APPLIED` is a status value only in this packet. It does not authorize automatic code edits.

## Fail-Closed Rules

Return `NOT_READY` or `NEEDS_SUPERVISOR` when:

- any reviewer, bot, review item, or check cannot be classified
- any blocking review thread is unresolved
- required CI failed, was cancelled, or is missing
- proof is stale, missing, or lacks a valid supervisor-accepted self-reference exception
- embedded audit is absent, skipped, failed, or stale
- GitHub auth or API state cannot be proven
- any requested action would mutate GitHub state

Return `BLOCKED` when the harvest is incomplete, the PR is draft, or the PR is closed without explicit `--allow-closed`. Return `NEEDS_IMPLEMENTER` when concrete implementation work is required, such as unresolved threads or failed checks. Unknown or untrusted reviewers and bots always block `READY`.

Explicit known reviewer logins are trusted. GitHub `authorAssociation` values `OWNER`, `MEMBER`, and `COLLABORATOR` are also trusted unless a future policy overrides that rule. External unknown actors and unclassified bots block `READY`.

Resolved and outdated review threads are historical evidence, not active blockers. When a raw review comment is linked to a resolved or outdated thread, PR Steward clears the stale `MUST_FIX` classification instead of keeping a false active blocker behind.

Proof freshness is fail-closed by default. A proof may be treated as current either by exact PR head match or by an explicit `CURRENT_WITH_SELF_REFERENCE_EXCEPTION` record that includes supervisor acceptance and proof-only changed-file evidence under `proof/`.

## CLI

Repo-local invocation:

```bash
python -m tools.pr_steward.intake --repo DDD-Enterprises/dopemux-mvp --pr 704 --out /tmp/pr-steward-704 --strict --proof-path proof/TP-DMX-PR-STEWARD-001/PROOF.json
scripts/pr-steward --repo DDD-Enterprises/dopemux-mvp --pr 704 --out /tmp/pr-steward-704 --strict --proof-path proof/TP-DMX-PR-STEWARD-001/PROOF.json
```

Live mode fails closed when `--proof-path` is absent, unreadable, unparseable, or stale relative to the PR head SHA. Fixture mode may include proof state directly in `harvest.json`.

Fixture mode is the offline validation lane and must not require live GitHub:

```bash
python -m tools.pr_steward.intake --fixture-dir tests/fixtures/pr_steward/ready_all_green --repo DDD-Enterprises/dopemux-mvp --pr 704 --out /tmp/pr-steward-ready --strict
```

## Review Bundle

For PR Steward packets, `proof/<PACKET_ID>/review_bundle/` is the single supervisor upload unit. The generated PR Steward outputs from fixture or live smoke runs must be copied into `review_bundle/artifacts/`, or listed in `review_bundle/MANIFEST.json` as excluded with a reason.
