---
id: SYSTEM_TaskOrchestrator
title: System Taskorchestrator
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: System Taskorchestrator (reference) for dopemux documentation and developer
  workflows.
---
# SYSTEM_TaskOrchestrator

## 1. Purpose

Task Orchestrator is the workflow-coordination service surface for dopemux. In the inspected runtime code it exposes HTTP, WebSocket, and MCP surfaces for workflow idea/epic operations, project workflow views, PM-plane write routing, and cross-plane coordination.

Its canonical authority slice is narrow:
- workflow-significant API behavior and transition routing exposed by `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`, `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/api/project_workflow.py`, and `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/api/pm_tools.py`
- workflow service logic for ideas, epics, and promotions in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_service.py`

It does not own durable PM entity truth, chronicle truth, or structured retrieval truth. In the inspected path its workflow persistence is bridge-mediated custom-data storage, not a local Task Orchestrator database.

## 2. Core Responsibilities

- Exposes the active FastAPI runtime.
  Evidence: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` constructs `FastAPI(...)`, registers `/health`, `/info`, `/metrics`, workflow endpoints, coordination endpoints, and `/ws/coordination`.
- Serves workflow idea and epic CRUD-plus-promotion behavior.
  Evidence: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` defines `/api/workflow/ideas`, `/api/workflow/epics`, and promotion endpoints; `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_service.py` implements create, list, update, and promote behavior with version and idempotency checks.
- Serves project-scoped workflow read and transition surfaces.
  Evidence: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/api/project_workflow.py` defines `/api/projects/{project_id}/workflow/*` endpoints for queue, blockers, state, and transitions.
- Accepts PM-plane write requests through dedicated endpoints.
  Evidence: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/api/pm_tools.py` exposes `/api/pm/work-items/{task_id}/update`, `/transition`, and `/progress`, wiring them into `src/dopemux/pm/writes.py`.
- Publishes coordination and event-stream surfaces.
  Evidence: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` defines `/api/coordination/*` endpoints and `/ws/coordination`; `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/core/coordinator.py` manages event queues, handlers, conflict tracking, and plane-health state.
- Provides an MCP stdio entrypoint bound to the active runtime MCP object.
  Evidence: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/mcp_stdio.py` imports `mcp` from `app.main` and runs it with `transport="stdio"`.
- Persists workflow records through DopeconBridge custom-data categories instead of local storage.
  Evidence: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py` writes categories `workflow_ideas`, `workflow_epics`, and `workflow_audit` via `AsyncDopeconBridgeClient`.

## 3. Non-Responsibilities

- It does not own passive PM metadata authority.
  Evidence: `/Users/hue/code/dopemux-mvp/src/dopemux/pm/writes.py` classifies passive metadata writes under Leantime and reserves workflow-significant transitions for Task Orchestrator.
- It does not own chronicle authority.
  Evidence: `/Users/hue/code/dopemux-mvp/src/dopemux/pm/writes.py` mirrors progress into dope-memory; Task Orchestrator is not the chronicle writer there.
- It does not own structured decision/progress/context authority.
  Evidence: `/Users/hue/code/dopemux-mvp/src/dopemux/pm/writes.py` assigns canonical progress/decision writes to ConPort; Task Orchestrator is not the ConPort writer.
- It does not own DopeconBridge routing authority.
  Evidence: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py` depends on bridge custom-data APIs; the store is a bridge client, not the bridge runtime.
- It does not establish a single canonical agent runtime for the repo.
  Evidence: agent surfaces also exist under `/Users/hue/code/dopemux-mvp/services/agents` and `/Users/hue/code/dopemux-mvp/src/dopemux/agent_orchestrator.py`; repo-level agent authority remains unresolved in `TRUTH_GAPS.md`.

## 4. Key Surfaces

- Canonical runtime code: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`
- Canonical stdio MCP wrapper: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/mcp_stdio.py`
- Unsupported runtime variant: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py`
  This file exits immediately and says to use `app/main.py`.
- Container/runtime packaging surface: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/Dockerfile`
- Compose/runtime wiring: `/Users/hue/code/dopemux-mvp/compose.yml`, `/Users/hue/code/dopemux-mvp/docker/compose.core.yml`, `/Users/hue/code/dopemux-mvp/services/registry.yaml`

Active ports observed in code/config:
- `8000` is the current compose/registry/container port.
  Evidence: `/Users/hue/code/dopemux-mvp/compose.yml`, `/Users/hue/code/dopemux-mvp/docker/compose.core.yml`, and `/Users/hue/code/dopemux-mvp/services/registry.yaml` map Task Orchestrator to `8000`; `/Users/hue/code/dopemux-mvp/services/task-orchestrator/Dockerfile` sets `PORT=8000`, exposes `8000`, and health-checks `http://localhost:8000/health`.
- `3014` remains an intended or historical runtime port in code.
  Evidence: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` uses `os.getenv("PORT", 3014)` for `/info` and `__main__`; `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py` declares `app/main.py (Port 3014)`.

Primary APIs and transports:
- HTTP health and discovery: `/health`, `/info`, `/metrics`
- Workflow APIs: `/api/workflow/ideas*`, `/api/workflow/epics*`
- Project workflow APIs: `/api/projects/{project_id}/workflow/*`
- PM-plane APIs: `/api/pm/work-items/*`
- Coordination APIs: `/api/coordination/*`
- WebSocket transport: `/ws/coordination`
- MCP stdio transport: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/mcp_stdio.py`

Storage surfaces:
- No local Task Orchestrator database was observed in the inspected workflow path.
- Workflow persistence writes through DopeconBridge custom-data categories `workflow_ideas`, `workflow_epics`, and `workflow_audit` in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py`.

## 5. System Boundaries

- DopeconBridge
  Task Orchestrator sends workflow custom-data reads/writes through `AsyncDopeconBridgeClient` in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py`.
  It receives bridge-backed persistence and emits custom-data writes and bridge client calls.
  It does not control bridge routing policy or make the bridge authoritative.

- Leantime
  PM-plane write contracts in `/Users/hue/code/dopemux-mvp/src/dopemux/pm/writes.py` treat Leantime as the passive metadata authority and as a mirror target after workflow transitions.
  Task Orchestrator does not control Leantime’s canonical task metadata store.

- ConPort
  PM-plane progress/decision writes in `/Users/hue/code/dopemux-mvp/src/dopemux/pm/writes.py` treat ConPort as the canonical decision/context writer.
  Task Orchestrator may consume ConPort-adjacent adapters and event flows, but it does not own ConPort retrieval or graph truth.

- dope-memory
  PM-plane progress logging mirrors to dope-memory chronicle in `/Users/hue/code/dopemux-mvp/src/dopemux/pm/writes.py`.
  Task Orchestrator does not control chronicle durability or chronicle schema authority.

- ADHD Engine
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/core/coordinator.py` includes ADHD engine health checks and cognitive-plane coordination references.
  Task Orchestrator may query or coordinate with that service, but it does not own ADHD state models or runtime.

- dopemux PM helpers
  `/Users/hue/code/dopemux-mvp/src/dopemux/pm/reads.py` reads normalized queue, blockers, and workflow state from Task Orchestrator.
  Task Orchestrator serves workflow views to those helpers, but does not become the authority for all PM reads.

## 6. Authority Model

- Canonical
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` for the active HTTP/WebSocket/MCP runtime code surface.
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_service.py` for idea/epic workflow behavior.
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/api/project_workflow.py` for project workflow read/transition API behavior.

- Derived
  Workflow records stored under bridge custom-data categories by `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py`.
  These records are written by Task Orchestrator logic but persisted through DopeconBridge-backed storage rather than a local authoritative store.

- Operational
  `/Users/hue/code/dopemux-mvp/compose.yml`, `/Users/hue/code/dopemux-mvp/docker/compose.core.yml`, and `/Users/hue/code/dopemux-mvp/services/registry.yaml` for current exposed port `8000`.
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/mcp_stdio.py` for stdio MCP launch.

- Unknown
  The actually correct container startup path is unresolved because `/Users/hue/code/dopemux-mvp/services/task-orchestrator/Dockerfile` launches `uvicorn task_orchestrator.app:app --port 8000`, while `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py` hard-fails and says not to use that module.
  Repo-wide agent authority remains `UNKNOWN`; the Task Orchestrator agent package is only one competing family.

## 7. Known Drift / Issues

- Runtime entrypoint conflict:
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` is the active runtime code, but `/Users/hue/code/dopemux-mvp/services/task-orchestrator/Dockerfile` launches `task_orchestrator.app:app`, and `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py` immediately exits.
- Port drift:
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` defaults to `3014`, while `/Users/hue/code/dopemux-mvp/services/task-orchestrator/Dockerfile`, `/Users/hue/code/dopemux-mvp/compose.yml`, `/Users/hue/code/dopemux-mvp/docker/compose.core.yml`, and `/Users/hue/code/dopemux-mvp/services/registry.yaml` all use `8000`.
- Bridge-backed persistence means local storage ownership is absent:
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py` stores workflow data via DopeconBridge custom-data categories instead of a Task Orchestrator-owned database.
- Health-monitor target mismatch:
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/core/coordinator.py` checks ADHD engine health at `http://localhost:8080/health`, while `/Users/hue/code/dopemux-mvp/services/registry.yaml` defines ADHD engine as host `3025` and container `8095`.
- Mixed implementation maturity in coordinator health:
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/core/coordinator.py` reports several plane-health dependencies as placeholders returning `"healthy"` without observed real checks for Leantime, Task Master, Serena, or ConPort.
- Older docs can overstate a cleaner architecture than the runtime earns:
  repo-truth artifacts already record unresolved canonicality for Task Orchestrator in `/Users/hue/code/dopemux-mvp/tmp/dmx-chatgpt-project-truth-extraction-002/TRUTH_CANONICALS.md` and `/Users/hue/code/dopemux-mvp/tmp/dmx-chatgpt-project-truth-extraction-002/TRUTH_GAPS.md`.

## 8. Working Rules

- Treat `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` as the strongest runtime-code authority for this system.
- Treat `8000` as the current compose/registry/container port in this checkout.
- Preserve `3014` explicitly as unresolved intended or historical port truth still present in code.
- Do not document `task_orchestrator/app.py` as a usable runtime; it is a hard-failing path.
- Do not describe Task Orchestrator as owning its own workflow database unless that becomes true in runtime code.
- Treat bridge-mediated workflow storage as a dependency boundary, not as proof that DopeconBridge is the workflow authority.
- Treat PM metadata, ConPort decision/progress truth, and dope-memory chronicle truth as adjacent authorities, not as Task Orchestrator-owned surfaces.
- If operator guidance must mention startup commands, call out the current Dockerfile/runtime conflict instead of pretending it is settled.
