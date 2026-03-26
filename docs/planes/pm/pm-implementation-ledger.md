---
id: PM_IMPLEMENTATION_LEDGER
title: PM Plane Implementation Ledger (Post-Merge)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-22'
last_review: '2026-03-26'
next_review: '2026-06-22'
prelude: Post-merge PM-plane implementation ledger replacing the older Phase 0 gap view.
---

# PM Plane Implementation Ledger (Post-Merge)

**Status**: Active Ledger
**Baseline**: `origin/main` plus PM continuation packets `01` through `04`
**Replaces**: Phase 0 Gap View (`docs/planes/pm/pm-plane-gaps.md`)

This ledger records runtime truth, not target architecture prose. When the runtime diverges from the normalized PM-plane contract, the status is marked `partial` or `drifted` rather than promoted to `implemented`.

## 1. Normalized PM-plane tools

| Tool | Status | Runtime evidence | Notes |
|---|---|---|---|
| `pm_get_project_context` | Partial | `src/dopemux/pm/reads.py` | Exists, but currently returns a fail-closed Leantime envelope with empty `context_data`; it does not yet satisfy the ConPort-enriched contract described in the normalized tool docs. |
| `pm_get_priority_queue` | Implemented | `src/dopemux/pm/reads.py`; `services/task-orchestrator/app/api/project_workflow.py` | Normalized read exists and now routes to Task Orchestrator as the canonical workflow authority. |
| `pm_get_blockers` | Implemented | `src/dopemux/pm/reads.py`; `services/task-orchestrator/app/api/project_workflow.py` | Normalized read exists and now routes to Task Orchestrator with fail-closed envelopes. |
| `pm_get_workflow_state` | Implemented | `src/dopemux/pm/reads.py`; `services/task-orchestrator/app/api/project_workflow.py` | Normalized read exists and now routes to Task Orchestrator with explicit legality fields. |
| `pm_update_work_item` | Implemented | `src/dopemux/pm/writes.py` | Canonical metadata write exists and rejects workflow-significant payloads. |
| `pm_transition_work_item` | Partial | `src/dopemux/pm/writes.py`; `services/task-orchestrator/app/api/project_workflow.py` | Canonical write helper exists, but the project-scoped Task Orchestrator transition endpoint currently returns `legality_result="unavailable"` until a canonical runtime binding is added. |
| `pm_get_sprint_snapshot` | Partial | `src/dopemux/pm/reads.py` | Exists, but currently returns a fail-closed Leantime envelope with empty `snapshot_data`. |
| `pm_get_decision_context` | Implemented | `src/dopemux/pm/reads.py` | Normalized ConPort-backed decision-context read exists. |
| `pm_log_progress` | Implemented | `src/dopemux/pm/writes.py` | Canonical ConPort write exists with dope-memory mirror receipts. |
| `pm_get_work_chronicle` | Implemented | `src/dopemux/pm/chronicle.py` | Normalized dope-memory chronicle read exists with fail-closed behavior. |
| `pm_search_project_knowledge` | Missing | Not found under `src/dopemux/pm/` or service adapters | Target contract exists in docs only. |
| `pm_get_technical_context` | Missing | Not found under `src/dopemux/pm/` or service adapters | Target contract exists in docs only. |

## 2. Canonical runtime entrypoints

- **Canonical PM read entrypoint**: `src/dopemux/pm/reads.py`
- **Canonical PM write entrypoint**: `src/dopemux/pm/writes.py`
- **Canonical PM chronicle entrypoint**: `src/dopemux/pm/chronicle.py`
- **Canonical PM event envelope**: `src/dopemux/events/types.py` (`PMEvent`)

The duplicate legacy entrypoints `src/dopemux/pm/read.py` and `src/dopemux/pm/write.py` were removed during the PM continuation stack so the active runtime no longer has competing singular/plural PM modules.

## 3. Runtime truths now established

### Normalized workflow reads are present
- `pm_get_priority_queue`, `pm_get_blockers`, and `pm_get_workflow_state` now exist in `src/dopemux/pm/reads.py`.
- Their canonical backend is Task Orchestrator, not Leantime.
- `services/task-orchestrator/app/api/project_workflow.py` now passes those legality/blocker envelopes through instead of hard-coding `allowed` responses.

### PM write boundaries are enforced
- `src/dopemux/pm/writes.py` is the canonical mutation layer.
- `pm_update_work_item` rejects workflow-significant payloads.
- `pm_transition_work_item` and `pm_log_progress` return canonical receipts plus explicit mirror receipts and reconciliation state.

### PM event taxonomy is normalized
- `src/dopemux/events/types.py` defines the canonical `PMEvent` envelope.
- `src/dopemux/event_bus.py` and `services/dopecon-bridge/dopecon_bridge/event_bus.py` require `idempotency_key` and `source` for `pm.*` events.
- Taskmaster, Task Orchestrator, and bridge event emitters were normalized onto that envelope in the continuation stack.

### Bridge authority is narrower
- `services/dopecon-bridge/dopecon_bridge/services/task_integration.py` now reads queue state through the normalized PM read layer.
- The same adapter now requires an authoritative Task Orchestrator transition result before it mirrors status to Leantime.
- This removes the last active import of the legacy `dopemux.pm.write` module from the repo runtime.

## 4. Remaining drift and gaps

### Project-scoped transition binding is still missing
The Task Orchestrator project workflow route exists, but `services/task-orchestrator/app/api/project_workflow.py` currently returns a fail-closed `legality_result="unavailable"` envelope for generic transitions. That is deliberate runtime truth, not a successful workflow transition implementation.

### Project context and sprint snapshot are still thin
`pm_get_project_context` and `pm_get_sprint_snapshot` exist only as fail-closed Leantime-backed envelopes. They satisfy the naming contract, but not the full normalized data contract described in the PM-plane docs.

### Search and technical context surfaces are still absent
`pm_search_project_knowledge` and `pm_get_technical_context` remain documentation-level targets only.

## 5. Practical interpretation

The PM continuation stack changed the repo from "normalized PM tools missing" to "normalized PM tools partially present with explicit remaining gaps." The safe current summary is:

- PM read/write entrypoints exist in runtime code.
- Workflow reads now route to Task Orchestrator.
- Metadata writes resolve to Leantime; progress writes resolve to ConPort; chronicle reads resolve to dope-memory.
- Project-scoped workflow transition still fails closed until a canonical Task Orchestrator runtime binding is implemented.
- The PM plane is **in progress**, not yet a fully closed authority implementation.
