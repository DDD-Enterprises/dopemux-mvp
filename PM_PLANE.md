# PM_PLANE

## 1. Purpose

This document describes the PM plane as it is implemented in this repository today.

In this checkout, PM authority is split. The inspected code does not support a single-system PM authority claim. `src/dopemux/pm/writes.py` explicitly routes different PM write classes to different systems, and `src/dopemux/pm/reads.py` explicitly reads different PM views from different backends.

This document is evidence-backed and fail-closed. It does not claim a unified PM system unless the runtime code proves one. Where ownership remains unresolved, it is marked `UNKNOWN`.

## 2. PM Scope

PM-plane concerns in this repo are the work-management surfaces tied to:

- work item and task metadata such as title, description, assignee, labels, dates, estimates, notes, and linked identifiers
- workflow transitions and workflow legality such as queue order, blockers, allowed transitions, and status changes
- blocker handling, decomposition-adjacent queueing, and next-action style workflow views
- decisions and progress context when those records are directly tied to work items or project workflow
- historical PM receipts and chronicle traces written as mirrors of PM activity
- execution adjacency where it materially affects PM workflow state, especially task-orchestrator workflow runtime and dopetask handoff boundaries

This document does not extend PM authority into the full memory plane or retrieval plane. ConPort, dope-memory, and dope-context remain separate systems with narrower PM-adjacent roles.

## 3. PM Systems and Their Roles

### dopemux

`dopemux` is the PM-plane coordinator and normalization layer, not the PM system of record. `src/dopemux/pm/writes.py` classifies updates and routes them to Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts. `src/dopemux/pm/reads.py` exposes normalized PM read functions with explicit backend provenance.

`dopemux` does not own canonical PM entity storage, canonical workflow transition storage, or chronicle durability. `src/dopemux/pm/store.py` is an in-memory store for testing and bootstrapping, not production PM persistence. `src/dopemux/pm/models.py` and `src/dopemux/pm/events.py` define canonical models and deterministic envelopes, but they do not prove a deployed unified PM database.

### dopetask

`dopetask` is execution-adjacent to the PM plane. It is the observed external task runner behind `dopemux kernel`, reached through `scripts/taskx` and then `scripts/dopetask`.

It does not own PM metadata, workflow legality, structured decision/progress context, or historical PM authority. In this repo it is an execution engine, not a PM authority surface.

### task-orchestrator

`services/task-orchestrator` is the workflow coordination and PM write-normalization surface. `services/task-orchestrator/app/api/project_workflow.py` serves queue, blockers, workflow state, and transition endpoints. `services/task-orchestrator/app/api/pm_tools.py` exposes PM write routes that call the shared `src/dopemux/pm/writes.py` logic.

It does not own all PM truth. `src/dopemux/pm/writes.py` assigns only workflow-significant transitions to task-orchestrator. Passive metadata stays with Leantime, structured decision/progress logging stays with ConPort, and chronicle receipts stay with dope-memory. Its own workflow persistence is not a task-orchestrator-local database in the inspected path; `services/task-orchestrator/app/services/workflow_store.py` stores workflow ideas, epics, and audit records through DopeconBridge custom data categories.

### Leantime

Leantime is treated by the dopemux PM layer as PM metadata authority and sprint/project snapshot authority. `src/dopemux/pm/writes.py` routes passive metadata updates to `leantime_client.update_task(...)` and mirrors workflow transitions back to `leantime_client.update_status(...)`. `src/dopemux/pm/reads.py` uses `LeantimeJSONRPCClient` for sprint snapshots through `get_project(...)` and `get_tickets(...)`.

In this repo, Leantime is mostly reached through adapters and route builders rather than local application code. The repo does not prove Leantime as the owner of workflow legality, decision context, or chronicle history.

### ConPort

ConPort is the structured decision, progress, and project-context surface that participates in the PM plane. `src/dopemux/pm/reads.py` treats ConPort as canonical for project context and decision context. `src/dopemux/pm/writes.py` treats ConPort as the primary writer for progress and decision logging.

ConPort does not own passive PM metadata, canonical workflow transitions, or chronicle history. Its mutable progress model is PM-adjacent, not proof that it is the whole PM system of record.

### dope-memory

dope-memory is the durable historical receipt and chronicle sink for PM activity. `src/dopemux/pm/writes.py` mirrors progress and decision logging into dope-memory after the primary ConPort write. `src/dopemux/pm/reads.py` lists dope-memory only as a supporting source for decision context and project knowledge; it does not directly read dope-memory for queue, blockers, state, or sprint truth.

dope-memory does not own PM metadata, workflow legality, queue state, or canonical structured decision authority.

### dopecon-bridge

dopecon-bridge is operational glue, proxying, and compatibility routing. `services/dopecon-bridge/dopecon_bridge/routes.py` states that the active bridge is adapter and proxy only and must not act as canonical task, workflow, decision, or progress authority.

Within the PM plane it performs three kinds of work:

- routes adapter-safe PM operations to Leantime under `/route/pm`
- proxies ConPort custom-data, decision, and progress routes under `/kg/*`
- provides the storage path used by task-orchestrator workflow records through bridge custom-data categories

It does not own PM truth. Where it persists or proxies PM-adjacent data, it is still an operational path, not the canonical authority.

## 4. PM Read Paths

Observed PM read paths are split by concern.

### Project context and decision context

`src/dopemux/pm/reads.py` reads project context from `ConPortClient.get_active_context(...)` using `CONPORT_CONTEXT_URL`, defaulting to `http://localhost:3005`, and calls `GET /api/context/{workspace_id}`. The same file marks the result `canonical_backend="conport"` for `pm_get_project_context(...)`.

`src/dopemux/pm/reads.py` reads decision context through `ConPortAdapter.search_decisions(...)`, which defaults to `CONPORT_URL=http://localhost:3004` and calls `GET /api/decisions`. The result is again labeled `canonical_backend="conport"`.

This means PM context reads are already split inside the ConPort integration itself: one path uses the `3005` context client and another uses the `3004` adapter. That is observed drift, not a single clean read contract.

### Priority queue, blockers, and workflow state

`src/dopemux/pm/reads.py` treats task-orchestrator as canonical for:

- `pm_get_priority_queue(...)`
- `pm_get_blockers(...)`
- `pm_get_workflow_state(...)`

These calls go through `TaskOrchestratorAdapter`, which defaults to `TASK_ORCHESTRATOR_URL=http://localhost:8000` and calls:

- `GET /api/projects/{project_id}/workflow/queue`
- `GET /api/projects/{project_id}/workflow/blockers`
- `GET /api/projects/{project_id}/workflow/state`

The served implementations live in `services/task-orchestrator/app/api/project_workflow.py`. When `request.app.state.task_runtime` exists, queue and workflow state can be derived from runtime tasks plus an optional `pm_store`. When runtime is absent, queue and blockers are derived from stored workflow epics loaded through `WorkflowService` and bridge-backed custom data. This is one authority slice with two internal read modes.

### Sprint snapshot and PM record snapshot

`src/dopemux/pm/reads.py` treats Leantime as canonical for `pm_get_sprint_snapshot(...)`. It requires a numeric project id, connects through `LeantimeJSONRPCClient`, calls `get_project(...)` and `get_tickets(...)`, and labels the result `canonical_backend="leantime"`.

This read path is specific to project and ticket snapshot data. It is not used for queue legality, blockers, or decision context.

### What is not read from dope-memory

The PM read layer does not directly read dope-memory for project context, priority queue, blockers, workflow state, or sprint snapshot. In `src/dopemux/pm/reads.py`, dope-memory appears only as a supporting source annotation for decision context and project knowledge. No direct dope-memory HTTP read is used by the core PM read functions.

### UNKNOWN

The repo does not prove one canonical PM read path for:

- next-action beyond the queue head returned by task-orchestrator queue results
- decomposition authority
- project-scoped technical context ownership, because `pm_get_technical_context(...)` uses Serena and is execution-adjacent rather than a core PM state authority
- a unified PM reader that reconciles Leantime, task-orchestrator, and ConPort into one stored PM snapshot

## 5. PM Write Paths

Observed PM writes are also split by concern.

### Metadata updates

`src/dopemux/pm/writes.py` `pm_update_work_item(...)` treats Leantime as canonical for passive metadata. It rejects workflow-significant fields, fails closed if the Leantime client is missing, and calls `leantime_client.update_task(...)`. The returned receipt declares `canonical_system="leantime"`.

This is the clearest observed PM metadata write authority in the repo.

### Workflow transitions

`src/dopemux/pm/writes.py` `pm_transition_work_item(...)` treats task-orchestrator as canonical for workflow-significant transitions. It calls `orchestrator_client.transition(...)` first, then best-effort mirrors the resulting status into Leantime through `leantime_client.update_status(...)`. The returned receipt declares `canonical_system="task-orchestrator"` and includes Leantime mirror receipts.

The HTTP surface for this shared logic is `services/task-orchestrator/app/api/pm_tools.py` `POST /api/pm/work-items/{task_id}/transition`. The project-scoped workflow transition surface also exists in `services/task-orchestrator/app/api/project_workflow.py` `POST /api/projects/{project_id}/workflow/transition`.

Write ownership is therefore fragmented but explicit: workflow transitions are not owned by Leantime in the dopemux PM layer.

### Progress and decision logging

`src/dopemux/pm/writes.py` `pm_log_progress(...)` treats ConPort as canonical for progress and decision logging. It performs the primary write through `conport_client.record_progress(...)` and then mirrors to dope-memory through `memory_client.append_chronicle(...)`. The returned receipt declares `canonical_system="conport"`.

The bridge also exposes direct proxy writes to ConPort under:

- `POST /kg/decisions`
- `POST /kg/progress`
- `POST /kg/custom_data`

in `services/dopecon-bridge/dopecon_bridge/routes.py`. These are operational proxy paths to ConPort, not proof that bridge owns those writes.

### Workflow record persistence inside task-orchestrator

`services/task-orchestrator/app/services/workflow_store.py` writes workflow ideas, epics, and audit records through `AsyncDopeconBridgeClient.save_custom_data(...)` into categories:

- `workflow_ideas`
- `workflow_epics`
- `workflow_audit`

This is a real persistence path, but it is bridge-mediated custom-data storage rather than a task-orchestrator-owned database. It is operationally important and architecturally split.

### Bridge-mediated PM routing

`services/dopecon-bridge/dopecon_bridge/routes.py` `POST /route/pm` routes adapter-safe PM operations to Leantime-compatible tooling. It explicitly blocks workflow-significant mutations and fails closed for bridge-local status mutation and next-action mutation.

This is an operational path for safe PM routing. It is not canonical PM write ownership.

### Chronicle receipts and historical traces

dope-memory is the historical receipt target for PM progress and decision activity after the primary ConPort write. Its PM role is mirror and chronicle append, not canonical PM state mutation.

### Fragmentation statement

Write ownership is fragmented by design in the observed code:

- Leantime for passive metadata
- task-orchestrator for workflow-significant transitions
- ConPort for structured decision and progress context
- dope-memory for mirrored historical receipts
- dopecon-bridge for routing and proxying

The repo does not support a single PM writer claim.

## 6. Authority Model

Authority must be classified per PM slice, not per brand name.

### PM metadata authority

- canonical: Leantime, as used by `src/dopemux/pm/writes.py` `pm_update_work_item(...)`
- derived: any reflected status or metadata projections elsewhere
- operational: dopecon-bridge `/route/pm` safe routing into Leantime-compatible tools
- unknown: a repo-local canonical PM metadata store outside Leantime is not proven

### Workflow transition authority

- canonical: task-orchestrator, as used by `src/dopemux/pm/writes.py` `pm_transition_work_item(...)` and served by `services/task-orchestrator/app/api/project_workflow.py`
- derived: Leantime reflections after task-orchestrator transitions
- operational: bridge policy blocks and adapter routing around workflow mutations
- unknown: whether task-orchestrator runtime authority is consistently exercised through the intended `app/main.py` path in deployed packaging, because Docker and code paths conflict

### Structured decision and progress authority

- canonical: ConPort, as used by `src/dopemux/pm/writes.py` `pm_log_progress(...)` and `src/dopemux/pm/reads.py` project-context and decision-context reads
- derived: any bridge-normalized response bodies, event publications, or downstream retrieval views
- operational: bridge `/kg/*` proxy routes and task-orchestrator bridge-backed storage paths
- unknown: whether all PM-relevant decision/progress writers consistently target the same ConPort runtime surface, because the repo uses both `3004` and `3005` contracts

### Historical receipt authority

- canonical: dope-memory chronicle for PM historical receipt storage
- derived: Postgres mirror or recap/reflection outputs in the wider dope-memory system
- operational: PM mirror writes from dopemux and event-stream publication around them
- unknown: broader top-level memory ownership beyond the chronicle slice

### Execution authority

- canonical: dopetask for task execution after `dopemux kernel` handoff
- operational: task-orchestrator runtime queue/state views when they derive execution-adjacent readiness and blockers
- derived: PM-facing representations of runtime task state
- unknown: one unified execution authority across dopetask, task-orchestrator runtime tasks, and other agent/task families is not proven

## 7. Known Drift / Issues

- Bridge breadth vs non-authority is real drift. `services/dopecon-bridge/dopecon_bridge/routes.py` exposes `/route/pm`, `/kg/*`, and `/ddg/*`, but its module header explicitly says bridge must not be canonical task, workflow, decision, or progress authority.

- Task-orchestrator runtime authority remains split by legacy entrypoint presence, but the active adapter, compose, registry, Dockerfile, and `services/task-orchestrator/app/main.py` now align on `8000`. Remaining `3014` references should be treated as legacy or archival unless backed by current runtime code/config.

- PM reads use split ConPort ports. `src/dopemux/pm/reads.py` reads project context through `ConPortClient` defaulting to `3005`, but decision context through `ConPortAdapter` defaulting to `3004`. That is an observed interface split inside one PM backend role.

- Task-orchestrator workflow persistence is not task-orchestrator-local. `services/task-orchestrator/app/services/workflow_store.py` persists workflow ideas, epics, and audit via DopeconBridge custom-data categories. This means task-orchestrator serves workflow authority while depending on bridge-mediated storage.

- Leantime authority is partly adapter-shaped, not repo-local runtime-shaped. The PM layer treats Leantime as metadata and snapshot authority, but the repo mostly reaches it through JSON-RPC clients, normalized route builders, and reflections. Operators should not overclaim repo-local visibility into Leantime internals.

- `src/dopemux/pm/store.py` can look authoritative but is not. It is an in-memory store with bootstrap/test semantics, not the observed persistent PM authority path.

- `services/task-orchestrator/app/api/project_workflow.py` has two internal state derivation modes. With `task_runtime`, queue and state are derived from runtime tasks and optional `pm_store`; without it, they are derived from stored workflow epics. That is runtime split behavior inside the same API surface.

- dope-memory is PM-adjacent but not PM state authority. The repo makes this explicit, but its presence in PM mirror receipts can still mislead downstream readers into treating chronicle history as current PM truth.

## 8. Working Rules

- Trust Leantime for passive work-item metadata and project/ticket snapshot reads when the question is about PM record data rather than workflow legality.

- Trust task-orchestrator for workflow-significant transitions, queue, blockers, and workflow state. Do not let bridge or Leantime reflections override that slice.

- Trust ConPort for structured decision and progress context tied to work. Do not treat ConPort as the owner of all PM state.

- Treat dope-memory as historical receipt authority only. It preserves PM activity traces; it does not define current PM status, queue legality, or workflow truth.

- Treat dopecon-bridge as routing, proxy, and compatibility glue. Use it as an operational path only after identifying the real upstream authority behind the route.

- Preserve `UNKNOWN` when ownership is unresolved. Do not invent a single PM layer from dopemux models, bridge routes, task-orchestrator workflow APIs, and memory mirrors.

- Avoid false unification. If a PM question mixes metadata, transitions, decisions, and chronicle history, split the answer by authority slice instead of naming one system as owner.
