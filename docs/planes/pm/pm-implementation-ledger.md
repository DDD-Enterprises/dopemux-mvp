---
id: PM_IMPLEMENTATION_LEDGER
title: PM Plane Implementation Ledger (Post-Merge)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-22'
last_review: '2026-03-27'
next_review: '2026-06-22'
prelude: Post-merge PM-plane implementation ledger replacing the older Phase 0 gap view.
---

# PM Plane Implementation Ledger (Post-Merge)

**Status**: Active Ledger
**Baseline**: `origin/main` plus PM continuation packets `01` through `08`
**Replaces**: Phase 0 Gap View (`docs/planes/pm/pm-plane-gaps.md`)

This ledger records runtime truth, not target architecture prose. When the runtime diverges from the normalized PM-plane contract, the status is marked `partial` rather than promoted to `implemented`.

## 1. Normalized PM-plane tools

| Tool | Status | Runtime evidence | Notes |
|---|---|---|---|
| `pm_get_project_context` | Partial | `src/dopemux/pm/reads.py`; `src/dopemux/tools/conport_client.py` | ConPort-backed project context now returns backend data plus linked IDs. It remains partial because supporting Leantime and dope-memory references are not yet attached. |
| `pm_get_priority_queue` | Implemented | `src/dopemux/pm/reads.py`; `services/task-orchestrator/app/api/project_workflow.py` | Normalized read returns Task Orchestrator-backed queue data through the project-scoped workflow runtime. |
| `pm_get_blockers` | Implemented | `src/dopemux/pm/reads.py`; `services/task-orchestrator/app/api/project_workflow.py` | Normalized read returns Task Orchestrator-backed blocker state through the project-scoped workflow runtime. |
| `pm_get_workflow_state` | Implemented | `src/dopemux/pm/reads.py`; `services/task-orchestrator/app/api/project_workflow.py` | Normalized read returns Task Orchestrator-backed workflow legality and allowed transition data. |
| `pm_update_work_item` | Implemented | `src/dopemux/pm/writes.py` | Canonical metadata write exists and rejects workflow-significant payloads. |
| `pm_transition_work_item` | Implemented | `src/dopemux/pm/writes.py`; `services/task-orchestrator/app/api/project_workflow.py`; `src/dopemux/pm/adapters/orchestrator.py` | Canonical write now binds to the project-scoped Task Orchestrator transition route and returns real legality/result envelopes for supported transitions. |
| `pm_get_sprint_snapshot` | Partial | `src/dopemux/pm/reads.py`; `src/integrations/leantime_jsonrpc_client.py` | Leantime-backed sprint snapshot now returns project and ticket data. It remains partial because optional ConPort context attachments are not yet included and non-numeric project IDs fail closed. |
| `pm_get_decision_context` | Implemented | `src/dopemux/pm/reads.py` | Normalized ConPort-backed decision-context read exists. |
| `pm_log_progress` | Implemented | `src/dopemux/pm/writes.py` | Canonical ConPort write exists with dope-memory mirror receipts. |
| `pm_get_work_chronicle` | Implemented | `src/dopemux/pm/chronicle.py` | Normalized dope-memory chronicle read exists with fail-closed behavior. |
| `pm_search_project_knowledge` | Partial | `src/dopemux/pm/reads.py`; `services/genetic_agent/shared/mcp/dope_context_client.py` | Normalized dope-context search now exists and returns evidence objects with ranking/confidence metadata. It remains partial because supporting source joins are envelope-only. |
| `pm_get_technical_context` | Partial | `src/dopemux/pm/reads.py`; `services/genetic_agent/shared/mcp/serena_client.py` | Normalized Serena-backed technical context now exists and returns implementation findings. It remains partial because supporting ConPort/dope-context joins are envelope-only. |

## 2. Canonical runtime entrypoints

- **Canonical PM read entrypoint**: `src/dopemux/pm/reads.py`
- **Canonical PM write entrypoint**: `src/dopemux/pm/writes.py`
- **Canonical PM chronicle entrypoint**: `src/dopemux/pm/chronicle.py`
- **Canonical PM event envelope**: `src/dopemux/events/types.py` (`PMEvent`)

The duplicate legacy entrypoints `src/dopemux/pm/read.py` and `src/dopemux/pm/write.py` were removed during the PM continuation stack so the active runtime no longer has competing singular/plural PM modules.

## 3. Runtime truths now established

### Normalized workflow reads are now authoritative
- `pm_get_priority_queue`, `pm_get_blockers`, and `pm_get_workflow_state` now exist in `src/dopemux/pm/reads.py`.
- Their canonical backend is Task Orchestrator, not Leantime.
- `services/task-orchestrator/app/api/project_workflow.py` now serves runtime-backed queue, blocker, state, and transition envelopes instead of recursively calling back through the public PM read adapter.

### PM write boundaries and transition binding are enforced
- `src/dopemux/pm/writes.py` is the canonical mutation layer.
- `pm_update_work_item` rejects workflow-significant payloads.
- `pm_transition_work_item` and `pm_log_progress` return canonical receipts plus explicit mirror receipts and reconciliation state.
- `pm_transition_work_item` now binds through the project-scoped Task Orchestrator workflow route instead of the deprecated bridge-local transition path.

### PM event taxonomy is normalized
- `src/dopemux/events/types.py` defines the canonical `PMEvent` envelope.
- `src/dopemux/event_bus.py` and `services/dopecon-bridge/dopecon_bridge/event_bus.py` require `idempotency_key` and `source` for `pm.*` events.
- Taskmaster, Task Orchestrator, and bridge event emitters were normalized onto that envelope in the continuation stack.

### Bridge authority is narrower
- `services/dopecon-bridge/dopecon_bridge/services/task_integration.py` now reads queue state directly from the Task Orchestrator HTTP surface instead of importing `dopemux.pm.reads` inside the bridge container.
- The same adapter now requires an authoritative Task Orchestrator transition result before it mirrors status to Leantime.
- This removes the last active import of the legacy `dopemux.pm.write` module from the repo runtime.

## 4. Remaining drift and gaps

### Project scoping is still thin inside Task Orchestrator runtime views
The project-scoped Task Orchestrator route now returns real queue/blocker/state/transition data, but tasks without explicit project linkage are still treated as in-scope for the requested project. The route is authoritative for workflow state, but its project partitioning remains coarse.

### Project context and sprint snapshot are backend-backed but not fully enriched
`pm_get_project_context` now reads ConPort active context, and `pm_get_sprint_snapshot` now reads Leantime project/ticket data. Both remain partial because the richer supporting-source joins described in the PM docs are not yet populated.

### Search and technical context now exist but are thin wrappers
`pm_search_project_knowledge` and `pm_get_technical_context` now exist in runtime code and return normalized envelopes, but they currently expose only their canonical backend results plus provenance/supporting-source envelopes rather than richer cross-plane joins.

## 5. Practical interpretation

The PM continuation stack changed the repo from "normalized PM tools missing" to "normalized PM tools partially present with explicit remaining gaps." The safe current summary is:

- PM read/write entrypoints exist in runtime code.
- Workflow reads now route to Task Orchestrator.
- Metadata writes resolve to Leantime; progress writes resolve to ConPort; chronicle reads resolve to dope-memory.
- Project-scoped workflow reads and transitions are now bound to Task Orchestrator runtime state.
- The PM plane is **substantially implemented**, with remaining gaps concentrated in richer multi-source enrichment rather than missing canonical entrypoints.
