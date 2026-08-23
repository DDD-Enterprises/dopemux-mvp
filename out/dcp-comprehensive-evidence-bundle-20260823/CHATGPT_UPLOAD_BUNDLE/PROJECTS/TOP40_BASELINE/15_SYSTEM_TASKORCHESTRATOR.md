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

This service must not be confused with the upstream 13-tool stdio MCP Task Orchestrator container used by Codex and `dopemux mcp` local configs. The upstream stdio MCP runtime is launched through `[LOCAL_PATH_REDACTED]` and stores repo-scoped SQLite state under the operator's local data directory. The in-repo service described here is the Dopemux FastAPI workflow service.

Its canonical authority slice is narrow:
- workflow-significant API behavior and transition routing exposed by `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, and `[LOCAL_PATH_REDACTED]`
- workflow service logic for ideas, epics, and promotions in `[LOCAL_PATH_REDACTED]`

It does not own durable PM entity truth, chronicle truth, or structured retrieval truth. In the inspected path its workflow persistence is bridge-mediated custom-data storage, not a local Task Orchestrator database.

## 2. Core Responsibilities

- Exposes the active FastAPI runtime.
  Evidence: `[LOCAL_PATH_REDACTED]` constructs `FastAPI(...)`, registers `/health`, `/info`, `/metrics`, workflow endpoints, coordination endpoints, and `/ws/coordination`.
- Serves workflow idea and epic CRUD-plus-promotion behavior.
  Evidence: `[LOCAL_PATH_REDACTED]` defines `/api/workflow/ideas`, `/api/workflow/epics`, and promotion endpoints; `[LOCAL_PATH_REDACTED]` implements create, list, update, and promote behavior with version and idempotency checks.
- Serves project-scoped workflow read and transition surfaces.
  Evidence: `[LOCAL_PATH_REDACTED]` defines `/api/projects/{project_id}/workflow/*` endpoints for queue, blockers, state, and transitions.
- Accepts PM-plane write requests through dedicated endpoints.
  Evidence: `[LOCAL_PATH_REDACTED]` exposes `/api/pm/work-items/{task_id}/update`, `/transition`, and `/progress`, wiring them into `src/dopemux/pm/writes.py`.
- Publishes coordination and event-stream surfaces.
  Evidence: `[LOCAL_PATH_REDACTED]` defines `/api/coordination/*` endpoints and `/ws/coordination`; `[LOCAL_PATH_REDACTED]` manages event queues, handlers, conflict tracking, and plane-health state.
- Provides an MCP stdio entrypoint bound to the active runtime MCP object.
  Evidence: `[LOCAL_PATH_REDACTED]` imports `mcp` from `app.main` and runs it with `transport="stdio"`.
- Persists workflow records through DopeconBridge custom-data categories instead of local storage.
  Evidence: `[LOCAL_PATH_REDACTED]` writes categories `workflow_ideas`, `workflow_epics`, and `workflow_audit` via `AsyncDopeconBridgeClient`.

## 3. Non-Responsibilities

- It does not own passive PM metadata authority.
  Evidence: `[LOCAL_PATH_REDACTED]` classifies passive metadata writes under Leantime and reserves workflow-significant transitions for Task Orchestrator.
- It does not own chronicle authority.
  Evidence: `[LOCAL_PATH_REDACTED]` mirrors progress into dope-memory; Task Orchestrator is not the chronicle writer there.
- It does not own structured decision/progress/context authority.
  Evidence: `[LOCAL_PATH_REDACTED]` assigns canonical progress/decision writes to ConPort; Task Orchestrator is not the ConPort writer.
- It does not own DopeconBridge routing authority.
  Evidence: `[LOCAL_PATH_REDACTED]` depends on bridge custom-data APIs; the store is a bridge client, not the bridge runtime.
- It does not establish a single canonical agent runtime for the repo.
  Evidence: agent surfaces also exist under `[LOCAL_PATH_REDACTED]` and `[LOCAL_PATH_REDACTED]`; repo-level agent authority remains unresolved in `TRUTH_GAPS.md`.

## 4. Key Surfaces

- Canonical runtime code: `[LOCAL_PATH_REDACTED]`
- Canonical stdio MCP wrapper: `[LOCAL_PATH_REDACTED]`
- Upstream 13-tool stdio MCP launcher for Codex/local MCP clients: `[LOCAL_PATH_REDACTED]`
- Unsupported runtime variant: `[LOCAL_PATH_REDACTED]`
  This file exits immediately and says to use `app/main.py`.
- Container/runtime packaging surface: `[LOCAL_PATH_REDACTED]`
- Compose/runtime wiring: `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`

Active ports observed in code/config:
- `8000` is the current compose/registry/container port.
  Evidence: `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, and `[LOCAL_PATH_REDACTED]` map Task Orchestrator to `8000`; `[LOCAL_PATH_REDACTED]` sets `PORT=8000`, exposes `8000`, and health-checks `http://localhost:8000/health`.
- `3014` remains an intended or historical runtime port in code.
  Evidence: `[LOCAL_PATH_REDACTED]` uses `os.getenv("PORT", 3014)` for `/info` and `__main__`; `[LOCAL_PATH_REDACTED]` declares `app/main.py (Port 3014)`.

Primary APIs and transports:
- HTTP health and discovery: `/health`, `/info`, `/metrics`
- Workflow APIs: `/api/workflow/ideas*`, `/api/workflow/epics*`
- Project workflow APIs: `/api/projects/{project_id}/workflow/*`
- PM-plane APIs: `/api/pm/work-items/*`
- Coordination APIs: `/api/coordination/*`
- WebSocket transport: `/ws/coordination`
- MCP stdio transport: `[LOCAL_PATH_REDACTED]`

Storage surfaces:
- No local Task Orchestrator database was observed in the inspected workflow path.
- Workflow persistence writes through DopeconBridge custom-data categories `workflow_ideas`, `workflow_epics`, and `workflow_audit` in `[LOCAL_PATH_REDACTED]`.
- The upstream 13-tool stdio MCP Task Orchestrator uses a separate local SQLite database keyed by local git repository identity. That database is not the storage authority for the in-repo FastAPI workflow service.

## 5. System Boundaries

- DopeconBridge
  Task Orchestrator sends workflow custom-data reads/writes through `AsyncDopeconBridgeClient` in `[LOCAL_PATH_REDACTED]`.
  It receives bridge-backed persistence and emits custom-data writes and bridge client calls.
  It does not control bridge routing policy or make the bridge authoritative.

- Leantime
  PM-plane write contracts in `[LOCAL_PATH_REDACTED]` treat Leantime as the passive metadata authority and as a mirror target after workflow transitions.
  Task Orchestrator does not control Leantime’s canonical task metadata store.

- ConPort
  PM-plane progress/decision writes in `[LOCAL_PATH_REDACTED]` treat ConPort as the canonical decision/context writer.
  Task Orchestrator may consume ConPort-adjacent adapters and event flows, but it does not own ConPort retrieval or graph truth.

- dope-memory
  PM-plane progress logging mirrors to dope-memory chronicle in `[LOCAL_PATH_REDACTED]`.
  Task Orchestrator does not control chronicle durability or chronicle schema authority.

- ADHD Engine
  `[LOCAL_PATH_REDACTED]` includes ADHD engine health checks and cognitive-plane coordination references.
  Task Orchestrator may query or coordinate with that service, but it does not own ADHD state models or runtime.

- dopemux PM helpers
  `[LOCAL_PATH_REDACTED]` reads normalized queue, blockers, and workflow state from Task Orchestrator.
  Task Orchestrator serves workflow views to those helpers, but does not become the authority for all PM reads.

## 6. Authority Model

- Canonical
  `[LOCAL_PATH_REDACTED]` for the active HTTP/WebSocket/MCP runtime code surface.
  `[LOCAL_PATH_REDACTED]` for idea/epic workflow behavior.
  `[LOCAL_PATH_REDACTED]` for project workflow read/transition API behavior.

- Derived
  Workflow records stored under bridge custom-data categories by `[LOCAL_PATH_REDACTED]`.
  These records are written by Task Orchestrator logic but persisted through DopeconBridge-backed storage rather than a local authoritative store.

- Operational
  `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, and `[LOCAL_PATH_REDACTED]` for current exposed port `8000`.
  `[LOCAL_PATH_REDACTED]` for stdio MCP launch.
  `[LOCAL_PATH_REDACTED]` for the upstream 13-tool stdio MCP runtime used by Codex/local MCP config.

- Unknown
  The repo-wide relationship between the in-repo FastAPI workflow service and the upstream 13-tool stdio MCP Task Orchestrator remains a boundary, not a unified runtime contract.
  Repo-wide agent authority remains `UNKNOWN`; the Task Orchestrator agent package is only one competing family.

## 7. Known Drift / Issues

- Runtime entrypoint drift:
  `[LOCAL_PATH_REDACTED]` is the active runtime code, and the current Dockerfile launches `app.main:app` on port `8000`. Older docs and local MCP config may still point at `task_orchestrator.app`, which is an unsupported hard-failing entrypoint.
- Port drift:
  `[LOCAL_PATH_REDACTED]` defaults to `3014`, while `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, `[LOCAL_PATH_REDACTED]`, and `[LOCAL_PATH_REDACTED]` all use `8000`.
- Bridge-backed persistence means local storage ownership is absent:
  `[LOCAL_PATH_REDACTED]` stores workflow data via DopeconBridge custom-data categories instead of a Task Orchestrator-owned database.
- Health-monitor target mismatch:
  `[LOCAL_PATH_REDACTED]` checks ADHD engine health at `http://localhost:8080/health`, while `[LOCAL_PATH_REDACTED]` defines ADHD engine as host `3025` and container `8095`.
- Mixed implementation maturity in coordinator health:
  `[LOCAL_PATH_REDACTED]` reports several plane-health dependencies as placeholders returning `"healthy"` without observed real checks for Leantime, Task Master, Serena, or ConPort.
- Older docs can overstate a cleaner architecture than the runtime earns:
  repo-truth artifacts already record unresolved canonicality for Task Orchestrator in `[LOCAL_PATH_REDACTED]` and `[LOCAL_PATH_REDACTED]`.

## 8. Working Rules

- Treat `[LOCAL_PATH_REDACTED]` as the strongest runtime-code authority for this system.
- Treat `8000` as the current compose/registry/container port in this checkout.
- Preserve `3014` explicitly as unresolved intended or historical port truth still present in code.
- Do not document `task_orchestrator/app.py` as a usable runtime; it is a hard-failing path.
- Do not describe Task Orchestrator as owning its own workflow database unless that becomes true in runtime code.
- Treat bridge-mediated workflow storage as a dependency boundary, not as proof that DopeconBridge is the workflow authority.
- Treat PM metadata, ConPort decision/progress truth, and dope-memory chronicle truth as adjacent authorities, not as Task Orchestrator-owned surfaces.
- If operator guidance must mention startup commands, call out the current Dockerfile/runtime conflict instead of pretending it is settled.
