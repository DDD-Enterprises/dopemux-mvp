---
id: PM_PLANE_INVENTORY
title: Pm Plane Inventory
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Pm Plane Inventory (Phase 0) grounded in line-cited evidence extracts.
---
# PM Plane Inventory (Phase 0)

Status: evidence locked (no design proposals in this phase).

## Scope
- In: `services/task-orchestrator/**`, `services/taskmaster/**`, `src/dopemux/event_bus.py`, `src/dopemux/events/**`, `installers/leantime/**` when present.
- Out: service redesign, implementation proposals, code changes outside docs/evidence.

## Evidence Bundle
- Directory: `docs/planes/pm/_evidence/PM-INV-00.outputs/`
- Key run artifacts: `56_rg_check.nl.txt:L1-L7`, `50_search_rg.exit.txt:L1-L1`

## Observed Components

| Component | Observed runtime surface | Observed model/storage details | Evidence |
|---|---|---|---|
| task-orchestrator package | FastAPI entrypoint exposes `/health`, `/api/tools`, `/api/tools/{tool_name}`, and `/api/decompose`; startup initializes Leantime + Redis + ADHD monitor. | `OrchestrationTask` dataclass + `TaskStatus` enum are defined in package models. | `services/task-orchestrator/task_orchestrator/app.py:L97-L139`; `services/task-orchestrator/task_orchestrator/app.py:L55-L76`; `services/task-orchestrator/task_orchestrator/models.py:L13-L22`; `services/task-orchestrator/task_orchestrator/models.py:L34-L62`; `docs/planes/pm/_evidence/PM-INV-00.outputs/11_task_orchestrator_files.txt.nl.txt:L123-L128` |
| task-orchestrator integrations (within scoped files) | Core client wiring includes Leantime JSON-RPC client, Redis manager, and lazy ConPort adapter accessor. | Config includes `leantime_url`, `redis_url`, and `conport_url` env-backed settings. | `services/task-orchestrator/task_orchestrator/core.py:L31-L58`; `services/task-orchestrator/task_orchestrator/core.py:L139-L160`; `services/task-orchestrator/task_orchestrator/core.py:L235-L244`; `services/task-orchestrator/task_orchestrator/config.py:L28-L39` |
| taskmaster wrapper (`server.py`) | Wrapper launches external Task-Master process (`uvx` or `npx`) and proxies stdio; optional event bus integration guarded by import. | Event emission calls `self.event_bus.publish(...)`; wrapper docstring claims ConPort decision tracking. | `services/taskmaster/server.py:L3-L11`; `services/taskmaster/server.py:L95-L123`; `services/taskmaster/server.py:L27-L33`; `services/taskmaster/server.py:L133-L155`; `services/taskmaster/server.py:L52-L52` |
| taskmaster bridge adapter (`bridge_adapter.py`) | Adapter uses DopeconBridge client to create progress entries, publish task events, and call `route_pm`. | Status values shown in bridge calls are string statuses (`TODO`, `DONE`) rather than the task-orchestrator enum. | `services/taskmaster/bridge_adapter.py:L20-L23`; `services/taskmaster/bridge_adapter.py:L67-L90`; `services/taskmaster/bridge_adapter.py:L163-L173`; `services/taskmaster/bridge_adapter.py:L288-L310` |
| dopemux event bus + typed events | `EventBus` abstract interface defines `publish/subscribe/unsubscribe`; includes `InMemoryAdapter` and `RedisStreamsAdapter` implementations. | Typed event models live in `src/dopemux/events/types.py`; includes `ContextEvent.Action.DECISION_LOGGED`. | `src/dopemux/event_bus.py:L68-L80`; `src/dopemux/event_bus.py:L82-L126`; `src/dopemux/event_bus.py:L127-L167`; `src/dopemux/events/types.py:L23-L33`; `src/dopemux/events/types.py:L52-L66` |
| leantime installer script | Installer class exists and orchestrates preflight, docker install, taskmaster setup, integration setup, startup, and verification. | Installer config tracks Leantime, Task-Master, and ADHD toggles in one config dataclass. | `installers/leantime/install.py:L3-L7`; `installers/leantime/install.py:L44-L74`; `installers/leantime/install.py:L95-L157`; `docs/planes/pm/_evidence/PM-INV-00.outputs/41_leantime_files.txt.nl.txt:L3-L3` |

## Observed Task/Status Models

| Surface | Canonical object/type in scoped files | Status/state representation observed | Evidence |
|---|---|---|---|
| task-orchestrator | `OrchestrationTask` + `TaskStatus` enum | `pending`, `in_progress`, `completed`, `blocked`, `needs_break`, `context_switch`, `paused` | `services/task-orchestrator/task_orchestrator/models.py:L13-L22`; `services/task-orchestrator/task_orchestrator/models.py:L34-L43` |
| taskmaster wrapper + bridge | No explicit task dataclass in scoped taskmaster files | Wrapper emits `task.created` / `task.completed`; bridge writes status strings like `TODO` and `DONE` | `services/taskmaster/server.py:L133-L155`; `services/taskmaster/bridge_adapter.py:L67-L70`; `services/taskmaster/bridge_adapter.py:L288-L310` |
| dopemux typed events | `ContextEvent.Action` enum | Contains context action `decision_logged` (event vocabulary present) | `src/dopemux/events/types.py:L57-L64` |

## Unknown or Missing (Phase 0)

| Item not found / unresolved | Why it matters | Evidence of absence or unresolved status |
|---|---|---|
| `services/taskmaster/models.py` | No explicit task schema file in scoped taskmaster package. | `docs/planes/pm/_evidence/PM-INV-00.outputs/55_expected_presence_check.nl.txt:L2-L2`; `docs/planes/pm/_evidence/PM-INV-00.outputs/21_taskmaster_files.txt.nl.txt:L1-L10` |
| `services/taskmaster/main.py` | No separate main entrypoint file in scoped taskmaster package. | `docs/planes/pm/_evidence/PM-INV-00.outputs/55_expected_presence_check.nl.txt:L4-L4`; `docs/planes/pm/_evidence/PM-INV-00.outputs/21_taskmaster_files.txt.nl.txt:L1-L10` |
| Runtime decision-linkage implementation in scoped taskmaster files | Decision traceability cannot be confirmed from scoped runtime files (search returns only a comment line). | `docs/planes/pm/_evidence/PM-INV-00.outputs/54_taskmaster_traceability_rg.txt.nl.txt:L1-L1`; `services/taskmaster/server.py:L52-L52` |
