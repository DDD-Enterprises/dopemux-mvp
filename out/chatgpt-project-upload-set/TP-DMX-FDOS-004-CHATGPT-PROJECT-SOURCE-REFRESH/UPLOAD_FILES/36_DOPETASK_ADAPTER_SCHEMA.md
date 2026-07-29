---
id: ADAPTER_SCHEMA
title: Adapter Schema
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Adapter Schema (explanation) for dopemux documentation and developer workflows.
---
# Adapter Schema — Canonical JSON Field Reference

## Root Object

```json
{
  "source": "dopetask",
  "schema_version": "1.0",
  "tp": { ... },
  "target": { ... },
  "posture": { ... },
  "summary": { ... },
  "proof": { ... },
  "governance": { ... },
  "operator_view": { ... },
  "integration": { ... },
  "computed_at": 1710000000.0
}
```

---

## `tp` — DopetaskTPIdentity

| Field | Type | Required | Values / Notes |
|-------|------|----------|----------------|
| `id` | str | yes | e.g. `"TP-PRMS-052"` |
| `family` | str | yes | `"flight_deck"` |
| `lane` | str | yes | `"closed_loop"` \| `"patch"` \| `"fusion"` |
| `title` | str | yes | Human-readable label |
| `status` | str | yes | See TP_STATUS_VALUES |
| `run_id` | str | yes | ISO-8601 timestamp string |

**TP_STATUS_VALUES**: `PLANNED`, `IN_PROGRESS`, `VALIDATED`, `OPERATIONAL`, `BLOCKED`, `DEFERRED`, `FAILED`, `UNKNOWN`

---

## `target` — DopetaskTarget

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `repo` | str | yes | Repository name |
| `worktree` | str | yes | Absolute path to worktree |
| `ref` | str | yes | Branch or ref name |
| `pr_number` | int\|null | no | PR number if applicable |
| `case_id` | str\|null | no | Case ID if applicable |

---

## `posture` — DopetaskPosture

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `mode` | str | yes | See POSTURE_MODE_VALUES |
| `advisory_only` | bool | yes | `true` only when mode=`ADVISORY_ONLY` |
| `signoff_required` | bool | yes | `true` for SUPERVISED and ADVISORY_ONLY |
| `defer_only` | bool | yes | `true` only when mode=`DEFER_ONLY` |
| `auto_apply_allowed` | bool | yes | `true` for GO_FULL_AUTO, LIVE_SAFE, GO_SUPERVISED_ONLY |
| `auto_apply_risk_threshold` | str | yes | `"LOW"` \| `"MEDIUM"` \| `"HIGH"` |

**POSTURE_MODE_VALUES**: `ADVISORY_ONLY`, `GO_SUPERVISED_ONLY`, `LIVE_SAFE`, `DEFER_ONLY`, `GO_FULL_AUTO`, `HOLD`, `UNKNOWN`

---

## `summary` — DopetaskSummary

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `result` | str | yes | Summary of what the engine determined |
| `next_action` | str | yes | Single human-readable operator instruction |
| `headline_state` | str | yes | See HEADLINE_STATE_VALUES |
| `confidence` | str | yes | `"HIGH"` \| `"MEDIUM"` \| `"LOW"` \| `"UNKNOWN"` |
| `risk` | str | yes | `"LOW"` \| `"MEDIUM"` \| `"HIGH"` \| `"UNKNOWN"` |
| `key_findings` | list[str] | yes | Notable findings (may be empty) |
| `key_caveats` | list[str] | yes | Caveats or warnings (may be empty) |

**HEADLINE_STATE_VALUES**: `READY`, `BLOCKED`, `DEFERRED`, `SUPERVISED`, `INCIDENT`, `UNKNOWN`

---

## `proof` — DopetaskProofRef

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `bundle_path` | str | yes | Path to manifest/bundle JSON |
| `bundle_present` | bool | yes | Whether bundle file exists |
| `archive_path` | str\|null | no | Path to .zip archive |
| `archive_present` | bool | yes | Whether archive exists (false if no archive_path) |
| `supporting_artifacts` | list[str] | yes | Additional artifact file paths |

---

## `governance` — DopetaskGovernance

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `allowed_actions` | list[str] | yes | Actions permitted under current posture |
| `blocked_actions` | list[str] | yes | Actions explicitly blocked |
| `signoff` | object | yes | See signoff sub-object |

**`governance.signoff`**:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `required` | bool | yes | Mirrors `posture.signoff_required` — NEVER independently set to false |
| `owner` | str | yes | Who must sign off (e.g. `"human_integrator"`) |
| `reason` | str | yes | Human-readable reason |

---

## `operator_view` — DopetaskOperatorView

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `open_first` | str | yes | Primary artifact path to open |
| `open_second` | str\|null | no | Secondary artifact path |
| `recommended_panel` | str | yes | `"mission_header"` \| `"detail"` \| `"summary"` |
| `artifact_priority` | list[str] | yes | Ordered list of artifact types |

---

## `integration` — DopetaskIntegration

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `loaded_from` | str | yes | `"bundle"` \| `"launch"` |
| `adapter_status` | str | yes | `"READY"` \| `"DEGRADED"` \| `"ERROR"` |
| `errors` | list[str] | yes | Fatal errors (empty if no errors) |
| `warnings` | list[str] | yes | Non-fatal warnings |

---

## `computed_at`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `computed_at` | float | yes | Unix timestamp (time.time()) when adapter ran |
