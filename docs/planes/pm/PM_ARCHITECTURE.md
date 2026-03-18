---
id: PM_ARCHITECTURE
title: Pm Architecture
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-13'
last_review: '2026-02-13'
next_review: '2026-05-14'
prelude: Evidence-locked PM plane architecture for canonical task state, event contracts, and storage boundaries.
---
# PM Architecture (Phase 3)

Status: proposed, evidence-locked redesign.
Scope: architecture and ADR decisions only; no implementation or schema changes in this packet.

## Observed Current State (Evidence)

- Task-orchestrator has an explicit task model and status enum, plus sync metadata and ADHD-specific fields in the orchestration object.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_task_orchestrator_models.py.txt:L13-L22`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_task_orchestrator_models.py.txt:L33-L63`.
- Task-orchestrator also has an explicit ConPort MCP wrapper for progress, decisions, linking, and search operations.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt:L7-L8`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt:L70-L210`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt:L298-L392`.
- Coordination logic is event-driven with task lifecycle processors and suppression telemetry; telemetry is a report layer, not canonical task state.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L188-L207`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L385-L430`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L889-L929`.
- Dopemux provides an event bus abstraction (in-memory and Redis adapters) and typed event models.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_event_bus.py.txt:L68-L82`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_event_bus.py.txt:L127-L175`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_events_types.py.txt:L23-L34`.
- Current Redis event bus path uses local fan-out fallback when disconnected, so event delivery guarantees are weak by default.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_event_bus.py.txt:L140-L156`.
- Taskmaster is currently thin: `server.py` wrapper + `bridge_adapter.py`, with entrypoint `taskmaster = taskmaster.server:main`; no separate `models.py` or `main.py` module exists.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/12_taskmaster_find_files.txt:L3-L10`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/99_missing_expected_files.txt:L1-L3`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_server.py.txt:L44-L53`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_src_dopemux_taskmaster.egg-info_entry_points.txt.txt:L1-L2`.
- Taskmaster bridge adapter currently creates ConPort/DopeconBridge progress entries and emits status-update events; it explicitly notes update-by-new-entry behavior is provisional.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L57-L79`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L122-L140`.
- CLI has task capture/listing commands and status panels, but defaults to broad multi-panel output when no status flags are set.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_cli.py.txt:L2220-L2241`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_cli.py.txt:L2455-L2501`.
- Leantime and taskmaster integration surfaces exist under `src/integrations/` and include bidirectional sync routines.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/10_conport_search.txt:L2-L20`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/10_conport_search.txt:L38-L110`.

## Canonical Task Object (Proposal)

The PM plane defines one canonical task object used for deterministic lifecycle transitions.

| Field | Type | Contract |
|---|---|---|
| `task_id` | string | Stable deterministic ID; never reassigned. |
| `title` | string | Required short user-visible title. |
| `body` | string nullable | Optional details or pointer text. |
| `status` \| enum \| Canonical enum: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `CANCELED`. |
| `phase` | string nullable | Optional workflow phase label. |
| `source` \| enum/string \| Creator/updater source (`task-orchestrator`, `taskmaster`, `leantime`, `cli`). |
| `created_at_utc` | RFC3339 UTC | Creation timestamp authority. |
| `updated_at_utc` | RFC3339 UTC | Monotonic update timestamp authority. |
| `version` | integer | Monotonic optimistic version for conflict refusal. |
| `provenance` \| object \| Actor/tool details (`actor_id`, `origin_command`, `source_event_id`). |
| `idempotency` \| object \| `transition_key` and optional `content_hash` for replay-safe writes. |
| `links.conport_progress_entry_id` | string nullable | Link to ConPort progress entry when present. |
| `links.conport_decision_ids` | list[string] | Linked decision IDs when present. |
| `links.chronicle_event_ids` | list[string] | Mirrored chronicle event IDs when present. |
| `links.external` \| object \| External refs (`leantime_ticket_id`, `taskmaster_tool_id`, `orchestrator_task_id`). |

Canonical invariants:

1. `task_id` immutable after creation.
1. `updated_at_utc` strictly monotonic per `task_id`.
1. Every transition request carries an idempotency key; duplicate keys are replay-safe no-ops.
1. Canonical write occurs at most once per accepted transition.
1. Default user output remains minimal with progressive disclosure gates (`--more`, `--why`, `--evidence`).
   Evidence: `docs/planes/pm/PM_OUTPUT_BOUNDARIES.md:L16-L33`.

Status dialect mapping into canonical enum:

- `pending`, `planned` -> `TODO`
- `in_progress` -> `IN_PROGRESS`
- `blocked` -> `BLOCKED`
- `completed`, `done` -> `DONE`
- `cancelled`, `canceled` -> `CANCELED`
- `needs_break`, `context_switch`, `paused` remain non-canonical advisory context (not lifecycle end-states).

Evidence for dialect drift requiring mapping: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_task_orchestrator_models.py.txt:L13-L22`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L69-L70`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_top10_services_dopecon-bridge_dopecon_bridge_models.py.txt:L25-L32`.

## Task Lifecycle

Canonical minimal lifecycle:

- `TODO`
- `IN_PROGRESS`
- `BLOCKED`
- `DONE`
- `CANCELED`

Allowed transitions:

- `TODO -> IN_PROGRESS | BLOCKED | CANCELED`
- `IN_PROGRESS -> BLOCKED | DONE | CANCELED`
- `BLOCKED -> TODO | IN_PROGRESS | CANCELED`
- `DONE -> (none)`
- `CANCELED -> (none)`

Transition rules:

1. Every accepted transition emits exactly one PM event.
1. Transition processing must be idempotent by `transition_key`.
1. Terminal states (`DONE`, `CANCELED`) reject non-idempotent reopening.

Refusal rules:

1. Reject unknown status values.
1. Reject stale `version` or non-monotonic `updated_at_utc`.
1. Reject transitions without idempotency key.
1. Reject source updates that cannot be mapped to canonical enum.

Evidence basis for current multi-surface lifecycle operations: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L191-L207`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L122-L146`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/10_conport_search.txt:L58-L110`.

## Storage, Derived, Mirrored

| Classification | Owner | Content | Write Contract |
|---|---|---|---|
| Stored (Canonical PM) | PM plane | Canonical task object fields and lifecycle version | Single canonical write per accepted transition; idempotent by key. |
| Stored (Memory/ConPort) | Memory plane | Decisions, rationale, and progress entries | PM links out to ConPort IDs; PM does not duplicate decision store internals. |
| Stored (Chronicle) | Memory capture path | High-signal PM events promoted for replay/audit | Mirror-only for PM; never source of canonical task truth. |
| Derived | PM telemetry | Suppression rates, signal/noise ratios, dashboards, rollups | Never treated as canonical truth. |
| Mirrored | Integration adapters | Optional sync projections to Leantime/taskmaster-facing views | Async projection from canonical PM state; retries are idempotent. |

Evidence:

- ConPort decision/progress write surfaces: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt:L70-L210`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt:L298-L392`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_top10_services_shared_conport_client_client.py.txt:L66-L137`.
- Telemetry as measurement surface: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L889-L929`.
- Existing sync projections: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/10_conport_search.txt:L58-L110`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_top10_services_dopecon-bridge_dopecon_bridge_services_task_integration.py.txt:L125-L154`.

UNKNOWN (evidence needed):

- Exact canonical PM persistence location/module in current codebase.
- Chronicle promotion contract for PM-only event subsets and retention windows.

## PM Event Taxonomy

Canonical PM events (new namespace):

- `pm.task.created`
- `pm.task.updated`
- `pm.task.status_changed`
- `pm.task.blocked`
- `pm.task.completed`
- `pm.decision.linked`
- `pm.sync.leantime.requested`
- `pm.sync.leantime.succeeded`
- `pm.sync.leantime.failed`

Required event fields:

- `event_id` (content-address hash of canonical payload)
- `task_id`
- `event_type`
- `ts_utc`
- `source`
- `idempotency_key`
- `payload` (minimal delta)

Idempotency contract:

- Duplicate `event_id` is a no-op.
- Duplicate `idempotency_key` for same `task_id` is a no-op.
- Consumers must be replay-safe.

Evidence for current fragmented event naming/surfaces: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L22-L47`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L82-L90`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L131-L140`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_events_types.py.txt:L23-L34`.

## Failure Modes and Degraded Mode

### ConPort unavailable

- Behavior: reject ConPort-linking operations as `DEGRADED_DEPENDENCY_UNAVAILABLE`.
- Canonical task transition may proceed only if request does not require immediate ConPort side effects.
- No fabricated `conport_progress_entry_id` or decision links.

Evidence: ConPort operations are explicit and can throw/fail at call boundary.
`docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt:L121-L123`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt:L165-L167`.

### EventBus unavailable

- Behavior: canonical transition is recorded once, event dispatch marked pending retry; caller receives explicit degraded result.
- Fail-closed requirement: no silent success for downstream fan-out.

Evidence: current bus path already warns and falls back locally when disconnected, so explicit degraded signaling is required to avoid silent drift.
`docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_event_bus.py.txt:L141-L156`.

### Taskmaster process unavailable

- Behavior: refuse taskmaster-sourced operations with explicit dependency error; other sources may proceed.
- Fail-closed requirement: do not infer taskmaster completion/state when wrapper process failed to start.

Evidence: wrapper starts external process and exits on startup failure.
`docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_server.py.txt:L95-L131`.

### Telemetry missing

- Behavior: continue canonical lifecycle operations; suppress telemetry panels and mark observability degraded.
- Guardrail: telemetry never used as canonical truth.

Evidence: telemetry reported via `get_suppression_report`, separate from lifecycle writes.
`docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L889-L929`.

## Interfaces to Existing Components

### Task-orchestrator compatibility

- Remains coordinator and sync engine.
- Consumes/emits PM events and maps existing status dialects into canonical enum.
- ConPort interactions remain adapter-based through MCP client wrappers.

Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L188-L207`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_conport_mcp_client.py.txt:L70-L210`.

### Taskmaster compatibility

- Treated as tool-wrapper and adapter surface, not canonical task authority.
- Wrapper keeps process proxy role; adapter emits integration events and routes to PM plane.

Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_server.py.txt:L44-L53`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_server.py.txt:L95-L131`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L57-L94`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_src_dopemux_taskmaster.egg-info_entry_points.txt.txt:L1-L2`.

### CLI compatibility

- CLI remains capture/shell surface for user actions and views.
- CLI does not become canonical task state holder in this design; it sends canonical transition requests and renders minimal output by default.

Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_cli.py.txt:L2220-L2241`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_cli.py.txt:L2455-L2501`; `docs/planes/pm/PM_OUTPUT_BOUNDARIES.md:L16-L33`.

## Open Questions

1. Where should canonical PM task persistence live in existing service topology?
Evidence needed: concrete module and storage contract in active runtime path (not design docs).

1. What is the exact write-through contract between canonical PM transitions and Chronicle promotion?
Evidence needed: concrete promotion adapter and retention rules for PM event subsets.

1. Should `paused`, `needs_break`, and `context_switch` become canonical states or remain advisory overlays?
Evidence needed: user-facing semantics contract and migration plan for existing status values.

1. What fields are mandatory inputs to compute `event_id` hash across all producers?
Evidence needed: cross-service event normalization spec covering CLI, task-orchestrator, and taskmaster wrappers.

1. Is dopecon-bridge `tasks` table a PM projection or a competing source of truth in current deployments?
Evidence needed: runtime ownership contract between PM plane and dopecon-bridge task integration path.
Evidence surface: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_top10_services_dopecon-bridge_dopecon_bridge_models.py.txt:L46-L65`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_top10_services_dopecon-bridge_dopecon_bridge_services_task_integration.py.txt:L47-L68`.
