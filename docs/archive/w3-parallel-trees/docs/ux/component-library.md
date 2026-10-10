---
id: COMPONENT_LIBRARY
title: Component Library
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Component Library (explanation) for dopemux documentation and developer workflows.
---
# Component Library — Operator Cockpit Components

All 8 components are implemented in `src/dopemux_pr_merge_specialist/ux_engine.py`
as methods of `RichTerminalRenderer`.

---

## 1. `mission_header_card`

**Purpose**: Primary situational header for a PR.

| Field           | Type   | Required | Description                                    |
|-----------------|--------|----------|------------------------------------------------|
| `pr_id`         | str    | Yes      | PR number                                      |
| `repo`          | str    | Yes      | `owner/repo` string                            |
| `state`         | str    | Yes      | PR state (READY, BLOCKED, SUPERVISED …)        |
| `posture`       | str    | Yes      | Operator posture (GO_SUPERVISED_ONLY …)        |
| `risk`          | str    | Yes      | Risk level (LOW / MEDIUM / HIGH)               |
| `confidence`    | str    | Yes      | Confidence score or label                      |
| `mission_line`  | str    | Yes      | One-line mission statement                     |
| `return_obj`    | bool   | No       | Return Rich Panel instead of printing          |

**RICH render**: Rich Panel containing a grid of key-value rows.

**PLAIN render**:
```
=== PR #123 [BLOCKED] | org/repo | posture=GO_SUPERVISED_ONLY | risk=HIGH | conf=0.82
MISSION: Resolve CI failure and re-queue for merge.
```

---

## 2. `next_action_card`

**Purpose**: Highlight the single most important operator action.

| Field        | Type | Required | Description              |
|--------------|------|----------|--------------------------|
| `command`    | str  | Yes      | CLI command to run       |
| `reason`     | str  | Yes      | Why this action          |
| `severity`   | str  | Yes      | HIGH / MEDIUM / LOW      |
| `return_obj` | bool | No       | Return Rich Panel        |

**PLAIN render**: `>> NEXT ACTION: [command] reason [severity=HIGH]`

---

## 3. `blocker_table`

**Purpose**: Tabulate all active blockers.

| Field        | Type      | Required | Description                            |
|--------------|-----------|----------|----------------------------------------|
| `blockers`   | list[any] | Yes      | List of blocker dicts or dataclasses   |
| `return_obj` | bool      | No       | Return Rich Table                      |

Blocker items may be `BlockerEvidence` dataclasses or plain dicts with keys:
`id`, `type`, `description`, `severity`.

**PLAIN render**: Text list with `[SEVERITY] #ID [TYPE] description`.

---

## 4. `strategy_comparison_table`

**Purpose**: Compare available merge strategies, highlighting the selected one.

| Field         | Type         | Required | Description                              |
|---------------|--------------|----------|------------------------------------------|
| `strategies`  | dict or list | Yes      | `STRATEGY_LIBRARY` dict or list          |
| `selected_id` | str          | Yes      | ID of currently selected strategy        |
| `return_obj`  | bool         | No       | Return Rich Table                        |

**RICH render**: Rich Table with selected row highlighted in bold green with `◀` marker.

**PLAIN render**: Text table with `*` prefix on selected row.

---

## 5. `stage_progress_rail`

**Purpose**: Visualise pipeline stage progression.

| Field        | Type      | Required | Description                                  |
|--------------|-----------|----------|----------------------------------------------|
| `stages`     | list[any] | Yes      | List of stage dicts or `RemediationStageResult` |
| `return_obj` | bool      | No       | Return Rich Text / str                       |

Stage icons: `✅` DONE, `▶` ACTIVE, `⛔` BLOCKED, `○` PENDING, `❌` FAILED.

**PLAIN render**: `✅ INTAKE → ▶ TRIAGE → ○ VERIFY → ○ PLAN`

---

## 6. `signoff_panel`

**Purpose**: Display operator signoff status for a mutation-class action.

| Field            | Type | Required | Description                          |
|------------------|------|----------|--------------------------------------|
| `action_class`   | str  | Yes      | e.g. MERGE, APPLY_FIX, CLOSE         |
| `required`       | bool | Yes      | Whether signoff is required           |
| `owner`          | str  | Yes      | Operator who owns the signoff         |
| `state`          | str  | Yes      | PENDING_SIGNOFF / APPROVED / NOT_REQUIRED |
| `last_timestamp` | str  | Yes      | ISO timestamp or epoch string         |
| `return_obj`     | bool | No       | Return Rich Panel                     |

---

## 7. `artifact_index_panel`

**Purpose**: Index of proof artifacts produced for a run.

| Field        | Type          | Required | Description                           |
|--------------|---------------|----------|---------------------------------------|
| `artifacts`  | dict or list  | Yes      | Artifact key-value map or list        |
| `return_obj` | bool          | No       | Return Rich Table                     |

Values truncated at 40 chars in PLAIN mode, 50 in RICH.

---

## 8. `monitoring_health_panel`

**Purpose**: Display rolling-window health metrics.

| Field         | Type | Required | Description                               |
|---------------|------|----------|-------------------------------------------|
| `health_data` | dict | Yes      | Output of `compute_rolling_health()` etc. |
| `return_obj`  | bool | No       | Return Rich Table                         |

Rows color-coded in RICH mode: green for healthy, red for degraded.
`THIN_SAMPLE` badge shown when `health_data["thin_sample"] is True`.

**PLAIN render**: Text list with `THIN_SAMPLE` note appended when thin.
