---
id: PCP-PR-STEWARD-READINESS
title: PCP Core PR Steward Proof-Readiness Intake
type: reference
owner: '@hu3mann'
author: claude
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: PCP Core PR Steward Proof-Readiness Intake (explanation) for dopemux documentation
  and developer workflows.
---
# PCP Core PR Steward Proof-Readiness Intake

## Overview

The PCP-Core PR Steward readiness intake is a **generic, project-agnostic** read-only harness that harvests PR state and emits a structured `MERGE_READINESS` signal.

This component is **ADVISORY only**. It never merges, sets a PR ready, or mutates any repository resource. READY is fail-closed: it is withheld on any blocking condition.

> **AIR Red Lines #7 and #8**: Green CI is NOT semantic proof. Automated checks passing does not mean the implementation is correct, the proof bundle is fresh, or the diff is within scope. READY requires explicit semantic proof — a proof artifact whose recorded head SHA matches the PR head SHA.

---

## The MERGE_READINESS Signal

Schema: `schemas/project_control_plane/merge_readiness.schema.json` (JSON Schema Draft 2020-12).

Module: `src/dopemux/pcp/pr_steward.py`

### Signal fields

| Field | Type | Description |
|---|---|---|
| `schema_version` | `const "pcp.merge_readiness.v0"` | Sentinel identifying schema version |
| `pr_ref` | object | PR identity: `repo`, `number`, `head_ref`, `base_ref` |
| `head_sha` | string (40 or 64 hex) | Head commit SHA at harvest time |
| `status` | enum | `READY`, `BLOCKED`, or `NEEDS_SUPERVISOR` |
| `blocked_reasons` | array of enum | Enumerated reasons READY was withheld |
| `intake` | object | Harvested evidence (see below) |
| `advisory` | `const true` | Always true — this signal is never a merge authority |
| `created_at` | date-time | ISO 8601 datetime of signal assembly |

### Intake fields (harvested evidence)

| Field | Type | Description |
|---|---|---|
| `intake_completeness` | object | Category-level completeness states for PR metadata, SHA, diff, review, comment, check, proof, allowlist, and security/release evidence |
| `changed_files` | array of string | Paths changed in the PR diff |
| `commits` | array of string | Commit SHAs in the PR |
| `checks` | array of objects | CI check results with `name`, `conclusion`, `stale_to_head` |
| `reviews` | array | Raw review objects (opaque to generic core) |
| `review_threads` | array of objects | Thread `resolved` and `blocking` flags |
| `reviewer_classifications` | array of objects | Actor `kind` (`HUMAN`, `KNOWN_BOT`, `UNKNOWN`) |
| `unclassified_review_items` | array of string | Review item IDs that could not be classified |
| `proof_refs` | array of objects | Proof artifact references with `path` and `head_sha` |
| `proof_freshness` | enum | `FRESH`, `STALE`, `MISSING`, or `UNKNOWN` |
| `diff_escapes_allowlist` | boolean | True if any file is outside the declared allowlist |
| `security_release_required` | boolean | True if security or release gate approval is required |
| `security_release_approved` | boolean | True if a qualifying human approver granted the gate |

---

## Fail-Closed Blocking Conditions

READY is withheld when **any** of the following conditions holds.

### Blocked reasons

| `blocked_reason` | Trigger condition |
|---|---|
| `STALE_PROOF` | `proof_freshness` is `STALE`, `MISSING`, or `UNKNOWN` |
| `FAILED_CHECK` | Any check has `conclusion == "FAILURE"` |
| `STALE_CHECK` | Any check has `stale_to_head == true` or `conclusion` in `{STALE, PENDING, UNKNOWN}` |
| `UNKNOWN_REVIEWER_OR_BOT` | Any `reviewer_classifications` entry has `kind == "UNKNOWN"` |
| `UNCLASSIFIED_REVIEW_ITEM` | `unclassified_review_items` is non-empty |
| `UNRESOLVED_BLOCKING_THREAD` | Any review thread has `blocking == true` and `resolved == false` |
| `DIFF_OUTSIDE_ALLOWLIST` | `diff_escapes_allowlist == true` |
| `MISSING_SECURITY_RELEASE_APPROVAL` | `security_release_required == true` and `security_release_approved == false` |
| `MISSING_REQUIRED_INTAKE` | `intake` is `null`, missing, or `head_sha` is falsy |
| `INCOMPLETE_INTAKE` | Any `intake_completeness` category is not `COMPLETE` |
| `UNKNOWN` | Reserved for unclassifiable blocking conditions |

### Status derivation

| Condition | Status |
|---|---|
| Zero blocked reasons | `READY` |
| Only `MISSING_SECURITY_RELEASE_APPROVAL` | `NEEDS_SUPERVISOR` |
| Any other blocked reason | `BLOCKED` |

### Schema-level fail-closed gates (allOf)

The schema enforces these rules structurally via `allOf` if/then constraints:

- **Gate (a)**: `status == READY` requires `blocked_reasons maxItems 0`, every `intake_completeness` category `const "COMPLETE"`, `proof_freshness const "FRESH"`, and `diff_escapes_allowlist const false`.
- **Gate (b)**: `status` in `{BLOCKED, NEEDS_SUPERVISOR}` requires `blocked_reasons minItems 1`.
- **Gate (c)**: `proof_freshness` in `{STALE, MISSING, UNKNOWN}` forces `status` to `{BLOCKED, NEEDS_SUPERVISOR}`.
- **Gate (d)**: `diff_escapes_allowlist == true` forces `status` to `{BLOCKED, NEEDS_SUPERVISOR}`.
- **Gate (e)**: `status == READY` requires `security_release_required == false` OR `security_release_approved == true` (schema-level defense-in-depth for the unapproved security gate).

---

## Public API

### `assess_merge_readiness`

```python
from dopemux.pcp.pr_steward import assess_merge_readiness

signal = assess_merge_readiness(
    intake,                        # dict from harvest_pr_intake
    pr_ref={"repo": "owner/repo", "number": 42,
            "head_ref": "feature/x", "base_ref": "main"},
    head_sha="abc123..." * 5,
    created_at="2026-06-22T00:00:00Z",
)
```

Pure, deterministic, fail-closed. Returns a dict matching `merge_readiness.schema.json`. Never calls external processes.

### `harvest_pr_intake`

```python
from dopemux.pcp.pr_steward import harvest_pr_intake

result = harvest_pr_intake(
    123,
    repo="owner/repo",
    runner=None,   # injectable for testing; None = default subprocess wrapper
)
```

Read-only harvester using `gh pr view`. Returns `{pr_ref, head_sha, intake}`. The `runner` parameter accepts a callable for injecting a fake in tests — no real subprocess runs in unit tests.

> **Note**: The raw harvest marks proof refs, proof freshness, review comments, issue comments, allowlist, and security/release approval as incomplete because `gh pr view` alone does not prove those categories. A harvested-only signal therefore can never be `READY` — callers must supply complete category evidence externally (for example, by reading proof artifacts, review/comment surfaces, allowlist results, and security/release approvals before calling `assess_merge_readiness`).

> **Note**: `stale_to_head` is derived from check conclusion only (`STALE`, `PENDING`, or `UNKNOWN` conclusions set it to `true`). The `gh statusCheckRollup` response is semantically head-scoped, so per-check SHA comparison is not attempted — `gh` does not expose an individual check-run SHA.

---

## Relationship to Existing Dopemux Machinery

This generic PCP-Core module **coexists with** and is **not a replacement for** the Dopemux-specific components:

- `tools/pr_steward/` — Dopemux-specific CLI and classifier that specialises this core.
- `.claude/skills/pr-merge-specialist/` — Dopemux skill integrating steward gate into the merge workflow.
- `contracts/openclaw-dcp-routing/pr_steward_merge_readiness.schema.json` — OpenClaw DCP routing contract (Draft 7; Dopemux-specific fields including `readiness`, `risk_tier`, `embedded_audit`, `proof.proof_freshness.status`).
- `schemas/pr_steward/merge_readiness.schema.json` — Dopemux internal schema (v1.1.0, richer `proof_freshness` object, `mutation_performed` guard).

The PCP-Core schema (`schemas/project_control_plane/merge_readiness.schema.json`) is the **project-agnostic foundation** from which Dopemux-specific schemas extend the concept. It shares field names where the semantics align but does not import or depend on any Dopemux-specific type.

---

## Tests

`tests/project_control_plane/test_pr_steward.py`

Covers: clean-intake READY path, one test per blocking condition, advisory/no-merge source assertion, fake-runner harvest pipeline, and schema Draft 2020-12 self-consistency.

Run with:

```bash
python -m pytest -q tests/project_control_plane/test_pr_steward.py
```
