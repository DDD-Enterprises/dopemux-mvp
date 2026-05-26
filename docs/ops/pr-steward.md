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
- proof does not match PR head SHA
- embedded audit is absent, skipped, failed, or stale
- GitHub auth or API state cannot be proven
- any requested action would mutate GitHub state
