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

This service must not be confused with the upstream 14-tool stdio MCP Task Orchestrator container used by Codex and `dopemux mcp` local configs. The upstream stdio MCP runtime is launched through `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh` and runs as a singleton Docker container (one per workspace) with container-local, volume-backed persistence. The in-repo service described here is the Dopemux FastAPI workflow service. See §9 for the full upstream-MCP coverage.

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
- Upstream 14-tool stdio MCP launcher for Codex/local MCP clients: `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh`
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
- The upstream stdio MCP Task Orchestrator (now 14 tools at v3.8.0) uses container-local storage managed inside a singleton Docker container scoped per workspace; persistence is volume-backed, not a repo-keyed SQLite file. That storage is not the authority for the in-repo FastAPI workflow service. See §9 below for the full upstream-MCP coverage.

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
  `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh` for the upstream 14-tool stdio MCP runtime used by Codex/local MCP config.

- Unknown
  The repo-wide relationship between the in-repo FastAPI workflow service and the upstream 14-tool stdio MCP Task Orchestrator remains a boundary, not a unified runtime contract.
  Repo-wide agent authority remains `UNKNOWN`; the Task Orchestrator agent package is only one competing family.

## 7. Known Drift / Issues

- Runtime entrypoint drift:
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` is the active runtime code, and the current Dockerfile launches `app.main:app` on port `8000`. Older docs and local MCP config may still point at `task_orchestrator.app`, which is an unsupported hard-failing entrypoint.
- Port drift:
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` defaults to `3014`, while `/Users/hue/code/dopemux-mvp/services/task-orchestrator/Dockerfile`, `/Users/hue/code/dopemux-mvp/compose.yml`, `/Users/hue/code/dopemux-mvp/docker/compose.core.yml`, and `/Users/hue/code/dopemux-mvp/services/registry.yaml` all use `8000`.
- Bridge-backed persistence means local storage ownership is absent:
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py` stores workflow data via DopeconBridge custom-data categories instead of a Task Orchestrator-owned database.
- Health-monitor target mismatch:
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/core/coordinator.py` checks ADHD engine health at `http://localhost:8080/health`, while `/Users/hue/code/dopemux-mvp/services/registry.yaml` defines ADHD engine as host `3025` and container `8095`.
- Mixed implementation maturity in coordinator health:
  `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/core/coordinator.py` reports several plane-health dependencies as placeholders returning `"healthy"` without observed real checks for Leantime, Task Master, Serena, or ConPort.
- Older docs can overstate a cleaner architecture than the runtime earns:
  repo-truth artifacts already record unresolved canonicality for Task Orchestrator in `/Users/hue/code/dopemux-mvp/docs/03-reference/truth/truth-canonicals.md` and `/Users/hue/code/dopemux-mvp/docs/03-reference/truth/truth-gaps.md`.

## 8. Working Rules

- Treat `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` as the strongest runtime-code authority for this system.
- Treat `8000` as the current compose/registry/container port in this checkout.
- Preserve `3014` explicitly as unresolved intended or historical port truth still present in code.
- Do not document `task_orchestrator/app.py` as a usable runtime; it is a hard-failing path.
- Do not describe Task Orchestrator as owning its own workflow database unless that becomes true in runtime code.
- Treat bridge-mediated workflow storage as a dependency boundary, not as proof that DopeconBridge is the workflow authority.
- Treat PM metadata, ConPort decision/progress truth, and dope-memory chronicle truth as adjacent authorities, not as Task Orchestrator-owned surfaces.
- If operator guidance must mention startup commands, call out the current Dockerfile/runtime conflict instead of pretending it is settled.

## 9. Upstream stdio MCP Task Orchestrator (separate runtime)

A distinct runtime from the in-repo FastAPI service in §§1-8. This is the upstream 14-tool stdio MCP container that holds canonical workflow-state authority per the accepted ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`. The two surfaces share the name "Task Orchestrator" but are not the same process and do not share storage.

Canonical operator floor for this runtime: [`.claude/CLAUDE.md` §Orchestrator Operations](../../../../.claude/CLAUDE.md). Canonical Codex floor: [`AGENTS.md` §12 Orchestrator Operations](../../../../AGENTS.md). Shared cross-agent protocol: [`docs/03-reference/orchestrator-note-filling-protocol.md`](../../orchestrator-note-filling-protocol.md).

### 9.1 Runtime identity

- **Image**: `ghcr.io/jpicklyk/task-orchestrator:v3.8.0` (as of 2026-05-27; verify via the wrapper script).
- **Launch wrapper**: `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh` (external to this repo; snapshot copies in [`scripts/external-references/`](../../../../scripts/external-references/) for traceability).
- **Container singleton policy**: `--name task-orchestrator-<workspace_id>` enforces one container per workspace. Opening a second Claude Code session in the same project disconnects the first session's MCP.
- **State storage**: container-local, volume-backed; not a repo-tracked file. Backups under `~/.local/share/dopemux-mission-control/task-orchestrator-backups/` per the recovery convention.
- **Transport**: stdio MCP — Claude Code, Codex, and Copilot all attach via the same wrapper.

### 9.2 Schema config (contract-sensitive)

Schema config is loaded by the container at startup from `.taskorchestrator/config.yaml` at the workspace root (see [contract-sensitive surfaces in governance-principles.md](../../../../.claude/modules/shared/governance-principles.md)). 8 schemas ship: `task-packet` (default for repo-changing work), `feature-implementation`, `bug-fix`, `rfc-proposal`, `audit-pack`, `sprint-goal`, `retrospective`, `default` (fallback). Each schema enumerates its required + advisory notes; selection is type-first, then tag-fallback, then default.

Editing `.taskorchestrator/config.yaml` requires ADR linkage + operator authorization per `AGENTS.md §6`.

### 9.3 The 14 MCP tools

| Tool | Purpose |
|---|---|
| `manage_items` | CRUD on work-items (create/update/delete). `type` field drives schema selection. |
| `query_items` | get / search / overview modes for reading work-items. |
| `manage_notes` | Upsert + delete notes; (itemId, key) is unique. |
| `query_notes` | get + list (no FTS on bodies in this version). |
| `manage_dependencies` | Intra-workflow BLOCKS edges with `unblockAt` thresholds. |
| `query_dependencies` | Reverse lookup (backlinks) + forward lookup. |
| `advance_item` | Trigger-based role transitions (start/complete/block/hold/resume/cancel/reopen). |
| `get_next_status` | Pure transition preview — what role an item would move to. |
| `get_next_item` | ADHD-ranked next-work recommendation. |
| `get_blocked_items` | Explicit BLOCKED + unsatisfied-dependency items. |
| `complete_tree` | Recursively complete an entire subtree. |
| `create_work_tree` | Atomic root + children + deps + optional notes. |
| `get_context` | Item / session-resume / health-check context snapshots. |
| `claim_item` | Optimistic-lock claim for worktree-parallel coordination. |

### 9.4 Workflow state machine

`queue → work → review → terminal`, with `blocked` as an out-of-band state that preserves `previousRole`. Triggers:

- `start`: advances by one role — queue → work, work → review, or review → terminal. Each step checks the *leaving* phase's required notes. Conventionally reserve `start` for queue→work / work→review; use `complete` for the final review→terminal transition.
- `complete`: any non-terminal/blocked → terminal. **Mechanical gate**: validates *all* required notes across *all* phases. For `task-packet` (and other change-producing schemas) this means the `proof-bundle` note (review phase, required) must be filed.
- `block` / `hold`: → blocked.
- `resume`: blocked → previousRole.
- `cancel`: → terminal with `statusLabel = "cancelled"`.
- `reopen`: terminal → queue (clears statusLabel; bypasses gates).

### 9.5 Gate enforcement (the proof-bundle complete-gate)

Per `AGENTS.md §9` Proof and Finality: no proof bundle means incomplete. The orchestrator enforces this mechanically — `advance_item(trigger="complete")` on a `task-packet` fails without the `proof-bundle` note. Other PAL-chain notes (`analyze`, `planner`, `codereview`, `precommit`) are advisory (required:false in Option A posture) but documented as the canonical chain per `AGENTS.md §5`.

### 9.6 Claim mechanism (multi-actor coordination)

Stage 1 trust: `claim_item` records self-reported actor IDs without authentication (`actor_authentication.enabled: false` in config). Convention: `{id: "worktree-<basename>-<branch>", kind: "subagent", parent: "<session-id>"}`. Acceptable for single-operator-per-project; flip to Stage 2 enforcement when multi-agent fleet semantics are required.

### 9.7 Boundary with the in-repo FastAPI service (§§1-8)

These two runtimes do not share workflow state. The upstream MCP owns work-item state, gates, claims, dependencies. The FastAPI service owns idea/epic/promotion CRUD via bridge custom-data. PM mirror writes (per `src/dopemux/pm/writes.py`) target Leantime + ConPort + dope-memory, not the upstream MCP. Cross-service consistency is operator-mediated, not runtime-enforced.

### 9.8 Cross-references

- [`.claude/CLAUDE.md`](../../../../.claude/CLAUDE.md) §Orchestrator Operations — Claude Code floor.
- [`AGENTS.md`](../../../../AGENTS.md) §5 (PAL chains), §6 (authorities), §9 (proof bundle), §12 (Orchestrator Operations).
- [`docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`](../../../90-adr/adr-task-orchestrator-as-workflow-authority.md) — accepted ADR.
- [`docs/90-adr/adr-task-orchestrator-claude-surface-integration.md`](../../../90-adr/adr-task-orchestrator-claude-surface-integration.md) — series ADR (DMX-ORCH-CLAUDE-SURFACE).
- [`docs/03-reference/orchestrator-note-filling-protocol.md`](../../../orchestrator-note-filling-protocol.md) — shared cross-agent note-filling protocol.
- [`.taskorchestrator/config.yaml`](../../../../.taskorchestrator/config.yaml) — schema config (contract-sensitive surface).
- [`.claude/modules/coordination/authority-matrix.md`](../../../../.claude/modules/coordination/authority-matrix.md) — system authority boundaries (task-orchestrator row covers this runtime).

### 9.9 Working rules for the upstream MCP runtime

- Treat `.taskorchestrator/config.yaml` as contract-sensitive — schema changes need ADR linkage + operator authorization.
- The wrapper script is **external** to this repo; do not modify it without explicit authorization. Snapshot copies in `scripts/external-references/` are reference-only.
- Set `type` at item creation for reliable schema activation; tag-only items fall through to `default`.
- File the `proof-bundle` note in review phase before `advance_item(trigger="complete")` — the gate is mechanical and unforgiving.
- For worktree-parallel work, use `claim_item` (read-only Stage 1 trust today; do not rely on it for adversarial multi-agent until Stage 2 ships).
- Do not duplicate workflow state in ConPort `progress_entry` / `custom_data`. ConPort retains decisions, knowledge graph, active_context — see authority-matrix.md violation rows.
