---
id: pm-plane-normalized-tool-surface
title: PM Plane Normalized Tool Surface
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-03-12'
next_review: '2026-06-10'
prelude: Normalized PM-plane tool contract that routes agents through canonical backends instead of subsystem-native seams.
---
# PM Plane Normalized Tool Surface

The PM plane exposes one normalized tool surface so agents interact with a stable contract instead of raw backend-native methods.

## Contract rules

- Every normalized tool has one canonical backend authority.
- Supporting sources may enrich responses, but they do not replace the canonical backend.
- Multi-plane reads must preserve provenance for canonical IDs, source planes, and derived evidence.
- Write-capable tools must be policy-wrapped and cannot bypass the PM-plane write adjudication model in [`pm-plane-write-adjudication-model.md`](pm-plane-write-adjudication-model.md).
- Raw subsystem-native surfaces are implementation details, not the long-term agent contract.

## Normalized tool list

| tool | purpose | mode | canonical backend authority | supporting sources | normalization requirements | provenance requirements | write-policy classification |
|---|---|---|---|---|---|---|---|
| `pm_get_project_context` | Return durable project context, decisions, and active context references. | read | `ConPort` | `Leantime`, `dope-memory` | Normalize context objects into one PM-plane envelope. | Include ConPort IDs and any supporting source references. | `safe_read_only` |
| `pm_get_priority_queue` | Return workflow-aware ordering of candidate work. | read | `Task Orchestrator` | `Leantime` | Normalize work items into canonical PM-plane task shape. | Include workflow authority source and reflected PM IDs. | `safe_read_only` |
| `pm_get_blockers` | Return current blocker state and dependency gating. | read | `Task Orchestrator` | `ConPort` | Normalize blocker classes and affected work IDs. | Include workflow source and any ConPort context IDs. | `safe_read_only` |
| `pm_get_workflow_state` | Return workflow legality and progression status for work items. | read | `Task Orchestrator` | `Leantime` | Normalize workflow and PM-facing status into distinct fields. | Include Task Orchestrator source plus reflected Leantime IDs. | `safe_read_only` |
| `pm_update_work_item` | Update PM-facing work-item metadata. | write | `Leantime` | `ConPort` for durable links | Normalize field names and reject workflow-significant payloads. | Return canonical Leantime IDs and any mirrored ConPort IDs. | `policy_wrapped_write` |
| `pm_transition_work_item` | Request a workflow-significant transition. | write | `Task Orchestrator` | `Leantime` reflection, `dope-memory` chronicle | Normalize requested transition and fail closed if adjudication surface is unavailable. | Return workflow authority source, canonical work ID, and mirror receipts. | `policy_wrapped_write` |
| `pm_get_sprint_snapshot` | Return PM-facing sprint state and operational work summary. | read | `Leantime` | `ConPort` | Normalize sprint/task payloads into PM-plane schema. | Include Leantime IDs and any attached ConPort context IDs. | `safe_read_only` |
| `pm_get_decision_context` | Return decision records and decision-linked durable context. | read | `ConPort` | `dope-memory` | Normalize decision records and linked work references. | Include ConPort decision IDs and chronicle references when present. | `safe_read_only` |
| `pm_log_progress` | Log durable progress against work or project context. | write | `ConPort` | `Leantime` reflection, `dope-memory` chronicle | Normalize progress vocabulary and require canonical work/reference IDs. | Return ConPort progress IDs and any mirror/chronicle IDs. | `policy_wrapped_write` |
| `pm_get_work_chronicle` | Return chronology, recap, replay, and work history. | read | `dope-memory` | `ConPort`, `Leantime` | Normalize chronicle events into timeline objects with linked references. | Include dope-memory IDs and referenced canonical source IDs. | `safe_read_only` |
| `pm_search_project_knowledge` | Retrieve ranked supporting evidence from indexed project artifacts. | read | `dope-context` | `ConPort`, `dope-memory`, `Leantime` | Normalize search hits into evidence objects with confidence/ranking metadata. | Always expose source plane and canonical source references when available. | `safe_read_only` |
| `pm_get_technical_context` | Return implementation-aware technical context for PM work. | read | `Serena` | `ConPort`, `dope-context` | Normalize technical findings into PM-safe summaries plus references. | Include Serena source plus links back to source systems. | `safe_read_only` |

## Backend mapping

- **Leantime**
  - `pm_update_work_item`
  - `pm_get_sprint_snapshot`
- **Task Orchestrator**
  - `pm_get_priority_queue`
  - `pm_get_blockers`
  - `pm_get_workflow_state`
  - `pm_transition_work_item`
- **ConPort**
  - `pm_get_project_context`
  - `pm_get_decision_context`
  - `pm_log_progress`
- **dope-memory**
  - `pm_get_work_chronicle`
- **dope-context**
  - `pm_search_project_knowledge`
- **Serena**
  - `pm_get_technical_context`

## Provenance contract

Whenever a tool pulls from more than one plane, the response must preserve:

- canonical backend name
- canonical IDs from that backend
- supporting source identifiers
- whether supporting records are canonical, mirrored, indexed, or derived

## Backend reality gaps

The current runtime has one important implementation gap:

- the active Task Orchestrator runtime does **not** expose project-scoped next-action, blocker, or transition endpoints yet

Implications:

- `pm_get_priority_queue`, `pm_get_blockers`, `pm_get_workflow_state`, and `pm_transition_work_item` are still canonically mapped to Task Orchestrator
- bridge implementations must fail closed or return an explicit unavailable/deferred result rather than invent local workflow truth
- no Leantime or bridge-local surface may claim to replace the missing Task Orchestrator runtime contract

## Never treat these as the long-term agent contract

The following backend-native surfaces remain implementation details and should not be exposed as the PM plane's stable interface:

- Leantime JSON-RPC method names such as `create_ticket`, `update_ticket`, or `list_tickets`
- raw Task Orchestrator MCP/HTTP tool names
- ConPort REST routes such as `/api/decisions` or `/api/progress`
- dope-memory HTTP internals
- dope-context backend-native search APIs
- Serena runtime-specific callable names
