---
id: pr-action-bridge
title: Pr Action Bridge
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-27'
last_review: '2026-05-27'
next_review: '2026-08-25'
prelude: Pr Action Bridge (explanation) for dopemux documentation and developer workflows.
---
# PR Action Bridge

**Module**: `tools/pr_action_bridge/compiler.py`
**Schema**: `schemas/pr_action_bridge/action_plan.schema.json`
**Tests**: `tests/pr_action_bridge/test_compiler.py`

## Overview

The PR Action Bridge compiler takes PR Steward artifacts and produces:

1. `ACTION_PLAN.json` — machine-readable action list validated against `action_plan.schema.json`
2. `REPAIR_PACKET.md` — human-readable repair instructions grouped by `target_role`

The compiler is a **pure function** — no filesystem I/O, no GitHub mutation, no subprocess calls.

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Pure function | `compile_action_plan(merge_readiness, review_ledger, thread_dispositions, ci_triage)` | Testable without I/O; caller owns persistence |
| No GitHub mutation | `mutation_performed: false` hardcoded | PR Steward v1 is check-only; action bridge is compiler/planner only |
| Action taxonomy | Locked to `classifier._readiness()` blocker taxonomy | Single source of truth for valid categories |
| EMBEDDED_AUDIT_* prefix | Maps to `embedded-audit-failed` / supervisor | All embedded audit failures require supervisor review |
| source_item_id | Cross-referenced from ledger/threads/ci_triage | Gives actionable pointer to the offending item |
| REPAIR_PACKET.md | Groups by role: supervisor → implementer → ci | Canonical role order matches escalation path |

## Usage

```python
from tools.pr_action_bridge.compiler import compile_action_plan

action_plan, repair_packet_md = compile_action_plan(
    merge_readiness=merge_readiness_json,
    review_ledger=review_ledger_json,
    thread_dispositions=thread_dispositions_json,
    ci_triage=ci_triage_json,
)

# Validate and persist
import json, jsonschema
schema = json.loads(Path("schemas/pr_action_bridge/action_plan.schema.json").read_text())
jsonschema.validate(action_plan, schema)
Path("ACTION_PLAN.json").write_text(json.dumps(action_plan, indent=2))
Path("REPAIR_PACKET.md").write_text(repair_packet_md)
```

## Output Shape

`ACTION_PLAN.json` fields:

| Field | Type | Description |
|---|---|---|
| `schema_version` | `"1.0.0"` | Fixed constant |
| `generated_at` | `str` | ISO 8601 UTC timestamp |
| `pr_number` | `int` | PR number from merge_readiness |
| `repo` | `str` | `owner/repo` |
| `readiness` | `str` | Copied from merge_readiness |
| `actions` | `Action[]` | Empty when `readiness=READY` |
| `mutation_performed` | `false` | Always false |

Each `Action`:

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Sequential ID, e.g. `action-0001` |
| `category` | `str` | Kebab-case category from blocker taxonomy |
| `target_role` | `str` | `supervisor` / `implementer` / `ci` |
| `source_blocker` | `str` | Exact blocker string from `merge_readiness.blockers` |
| `source_item_id` | `str\|null` | ID of the specific ledger/thread/ci item, or null |
| `rationale` | `str` | Human-readable explanation |

## Schema Invariant

When `readiness=READY`, `actions` must be an empty array (`maxItems: 0`). This is enforced by an `allOf` if/then in the schema.

## Action Taxonomy

Actions are locked to the blocker taxonomy from `classifier._readiness()`:

| Blocker | Category | Role |
|---|---|---|
| `HARVEST_INCOMPLETE` | `harvest-incomplete` | supervisor |
| `PR_IS_DRAFT` | `pr-is-draft` | supervisor |
| `PR_CLOSED` | `pr-closed` | supervisor |
| `MIXED_SHA_ARTIFACT_SET` | `mixed-sha` | supervisor |
| `UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION` | `unknown-reviewer` | supervisor |
| `PROOF_STALE` | `proof-stale` | supervisor |
| `PROOF_MISSING` | `proof-missing` | supervisor |
| `UNKNOWN_PR_AUTHOR` | `unknown-pr-author` | supervisor |
| `UNKNOWN_CHECK` | `unknown-check` | supervisor |
| `REVIEW_ITEM_NEEDS_SUPERVISOR` | `needs-supervisor` | supervisor |
| `EMBEDDED_AUDIT_*` (prefix) | `embedded-audit-failed` | supervisor |
| `UNRESOLVED_REVIEW_THREAD` | `unresolved-thread` | implementer |
| `FAILED_CHECK` | `failed-check` | implementer |
| `REQUEST_CHANGES` | `request-changes` | implementer |
| `REVIEW_ITEM_MUST_FIX` | `must-fix` | implementer |
| `PENDING_CHECK` | `pending-check` | ci |

## Governance

This module is **read-only**. It must never:

- Import `tools.pr_merge` or call `gh pr merge/approve/ready/comment`
- Write to GitHub, post comments, or approve PRs
- Execute subprocesses that mutate repository state

The static test `test_no_pr_merge_import` enforces this at test time.

## Related Files

- `tools/pr_steward/classifier.py` — canonical blocker taxonomy source
- `schemas/pr_steward/merge_readiness.schema.json` — primary input schema
- `docs/ops/operating-model.md` — governance context
- `docs/ops/tool-routing-matrix.md` — confirms PR Steward has no mutation route
