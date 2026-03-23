---
id: PM_IMPLEMENTATION_LEDGER
title: PM Plane Implementation Ledger (Post-Merge)
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-22'
last_review: '2026-03-22'
next_review: '2026-06-22'
prelude: Post-merge PM-plane implementation ledger replacing the older Phase 0 gap view.
---

# PM Plane Implementation Ledger (Post-Merge)

**Status**: Active Ledger
**Replaces**: Phase 0 Gap View (`docs/planes/pm/pm-plane-gaps.md`)

## 1. Normalized PM-Plane Tools

Based on the targets defined in `docs/90-adr/adr-pm-plane-authority-boundaries.md`, the implementation status of normalized PM-plane tools across all owned runtimes is as follows:

| Tool | Status | Evidence |
|---|---|---|
| `pm_get_project_context` | Missing | Not found in `src/` or `services/` |
| `pm_get_priority_queue` | Missing | Not found in `src/` or `services/` |
| `pm_get_blockers` | Missing | Not found in `src/` or `services/` |
| `pm_update_work_item` | Missing | Not found in `src/` or `services/` |
| `pm_get_sprint_snapshot` | Missing | Not found in `src/` or `services/` |
| `pm_get_decision_context` | Missing | Not found in `src/` or `services/` |
| `pm_get_work_chronicle` | Missing | Not found in `src/` or `services/` |
| `pm_search_project_knowledge` | Missing | Not found in `src/` or `services/` |
| `pm_get_technical_context` | Missing | Not found in `src/` or `services/` |

## 2. Architectural Gaps & Variants

### Active Task Orchestrator Runtime Variants
- **Core Orchestrator App:** `services/task-orchestrator/task_orchestrator/app.py`: FastAPI application exposing `/health`, `/api/tools`, and `/api/decompose`. (Evidence: `services/task-orchestrator/task_orchestrator/app.py:L55-L139`)
- **Decomposition Engine:** Uses Pal planner and has logic to sync to Leantime. (Evidence: `services/task-orchestrator/task_decomposition_endpoint.py:L62-L271`)
- **Sync Core:** Implements complex synchronization between Leantime, ConPort, and local systems. (Evidence: `services/task-orchestrator/app/core/sync.py:L4-L859`)

### Workflow Bypass Paths
- **Leantime Sync Bypass:** Sync operations in `sync.py` directly update Leantime tasks without explicit workflow routing enforcement, bypassing potential central orchestrator governance. (Evidence: `services/task-orchestrator/app/core/sync.py:L375-L480`)

### Bridge Shadow-Authority Paths
- **Taskmaster Bridge Adapter:** Uses DopeconBridge client to create progress entries and publish task events. Local task state and string statuses (`TODO`, `DONE`) are maintained, creating a shadow state compared to the authoritative `TaskStatus` enum. (Evidence: `services/taskmaster/bridge_adapter.py:L67-L90`, `L288-L310`)

### Taskmaster Traceability Gaps
- **Decision Linkage:** Scoped taskmaster runtime files do not show concrete decision-link linkage implementation; it relies only on descriptive comments. (Evidence: `services/taskmaster/server.py:L52`)

### CLI Orphan-State Gaps
- **Local Task Records:** The CLI creates tasks with a local `TaskRecord` representation that risks being orphaned if not synced cleanly back to ConPort/Leantime. (Evidence: `src/dopemux/adhd/task_decomposer.py:L40-L81`)
