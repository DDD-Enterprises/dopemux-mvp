# SYSTEM_ADHDEngine

## 1. Purpose

ADHD Engine is the repo's ADHD/operator-support service runtime. In the inspected code it runs as a FastAPI service from `services/adhd_engine/main.py`, mounts a FastMCP HTTP app under `/mcp`, and exposes ADHD-support endpoints from `services/adhd_engine/api/routes.py`.

Its canonical authority slice is narrow:
- current in-process ADHD support state held by the service runtime, including energy, attention, cognitive-load-adjacent snapshots, and detector/runtime buffers in `services/adhd_engine/core/engine.py`, `services/adhd_engine/main.py`, and `services/adhd_engine/api/routes.py`
- ADHD-support recommendations and assessments produced by its runtime logic and detectors in `services/adhd_engine/core/engine.py` and `services/adhd_engine/domains/*`
- ADHD Engine event emission and ADHD-focused hook/event handling surfaces implemented in `services/adhd_engine/event_emitter.py`, `services/adhd_engine/event_listener.py`, and hook-oriented routes in `services/adhd_engine/api/routes.py`

It is an operator-support / cognitive-state service. It does not own PM truth, workflow legality, chronicle authority, ConPort structured authority, retrieval truth, operator CLI control, or bridge authority. Where it writes or projects into other systems, those are downstream projections or integrations, not proof that ADHD Engine owns those systems' data.

## 2. Core Responsibilities

- Serves the active ADHD Engine HTTP runtime.
  Evidence: `services/adhd_engine/main.py` constructs `FastAPI(...)`, registers `/`, `/health`, `/metrics`, mounts `/mcp`, and includes `routes.router` under `/api/v1`.

- Maintains current ADHD/operator-support runtime state in-process and in Redis-backed service state.
  Evidence: `services/adhd_engine/core/engine.py` tracks `user_profiles`, `current_energy_levels`, `current_attention_states`, `active_accommodations`, cognitive-load/context-switch/break histories, monitor tasks, and Redis-backed profile loading. `services/adhd_engine/main.py` keeps a global `engine` instance and degraded fallback engine for partial startup.

- Produces ADHD-support assessments and recommendations.
  Evidence: `services/adhd_engine/main.py` MCP tools `get_cognitive_state` and `assess_task_complexity` call the engine directly. `services/adhd_engine/api/routes.py` exposes ADHD assessment, energy, attention, break, cognitive-load, flow-state, pattern, prediction, and statusline routes. `services/adhd_engine/core/models.py` defines energy, attention, cognitive-load, and recommendation models.

- Runs ADHD-related monitors, detectors, and support helpers.
  Evidence: `services/adhd_engine/core/engine.py` initializes `HyperfocusGuard`, `OverwhelmDetector`, `ProcrastinationDetector`, `WorkingMemorySupport`, `ContextPreserver`, `SocialBatteryMonitor`, and `VoiceAssistant`, then starts background monitoring.

- Exposes ADHD/operator-support APIs and local hook surfaces.
  Evidence: `services/adhd_engine/api/routes.py` serves `/assess-task`, `/energy-level/{user_id}`, `/attention-state/{user_id}`, `/recommend-break`, `/user-profile`, `/activity/{user_id}`, `/state`, `/log-intent`, `/save-context`, `/unfinished-work`, `/record-progress`, `/external-activity`, and `/log-git-event`, plus many additional ADHD-support endpoints. `/state`, `/log-intent`, `/save-context`, and related hook routes are explicitly documented in code as local hook support surfaces.

- Exposes MCP surfaces for ADHD support.
  Evidence: `services/adhd_engine/main.py` creates `FastMCP("ADHD-Engine")`, registers tools, mounts `mcp.http_app` at `/mcp`, and `services/adhd_engine/mcp_stdio.py` runs the same MCP object over stdio.

- Emits and consumes ADHD-relevant events where runtime wiring exists.
  Evidence: `services/adhd_engine/event_emitter.py` publishes structured events to Redis stream `dopemux:events`. `services/adhd_engine/event_listener.py` subscribes to `dopemux:events` and routes activity/session/progress/ADHD/calendar/Claude events to detectors and support helpers. `services/adhd_engine/main.py` attempts to start the event listener and workspace watcher only if `engine.event_bus` exists.

- Projects selected ADHD-related data into bridge/ConPort-adjacent storage and event paths.
  Evidence: `services/adhd_engine/bridge_integration.py` routes custom-data and progress-entry persistence through `DopeconBridgeClient`, with a local SQLite fallback. `services/adhd_engine/domains/task_enablement/working_memory_support.py` persists breadcrumbs/thought-like records through `bridge_client.log_custom_data(...)`. `services/dopecon-bridge/integrations/adhd_engine.py` defines buffered cognitive-state and overload/break event emission for bridge-side event flows. These are integration/projection paths, not stronger ADHD Engine authority claims over ConPort or the bridge.

## 3. Non-Responsibilities

- PM truth is not owned by ADHD Engine.
  Evidence: `docs/03-reference/planes/PM_PLANE.md` and `src/dopemux/pm/writes.py` split PM authority across Leantime, task-orchestrator, ConPort, and dope-memory. ADHD Engine is not named as canonical PM authority there.

- Workflow legality and workflow-significant PM transitions are not owned by ADHD Engine.
  Evidence: `docs/03-reference/systems/task-orchestrator/SYSTEM_TaskOrchestrator.md` assigns workflow-significant API behavior and transition routing to task-orchestrator. `services/adhd_engine/core/task_orchestrator_client.py` treats task-orchestrator as the service that performs decomposition coordination, ConPort persistence, and Leantime sync.

- Chronicle authority is not owned by ADHD Engine.
  Evidence: `docs/03-reference/systems/dope-memory/SYSTEM_DopeMemory.md` identifies dope-memory as the chronicle authority. ADHD Engine may emit events or project support data, but it is not the canonical chronicle ledger writer.

- ConPort structured authority is not owned by ADHD Engine.
  Evidence: `docs/03-reference/systems/conport/SYSTEM_ConPort.md` assigns structured decision, progress, context, and custom-data authority to ConPort. ADHD Engine writes through bridge/custom-data helpers and fallback adapters; that does not make it ConPort authority.

- Retrieval truth is not owned by ADHD Engine.
  Evidence: `docs/03-reference/systems/dope-context/SYSTEM_DopeContext.md` assigns retrieval/index behavior to dope-context. ADHD Engine may consume context-like signals or save context-adjacent data, but it does not own code/docs retrieval truth.

- Operator CLI control is not owned by ADHD Engine.
  Evidence: `docs/03-reference/systems/dopemux/SYSTEM_Dopemux.md` identifies `dopemux` as the operator-facing control layer and CLI package.

- Bridge authority is not owned by ADHD Engine.
  Evidence: `services/dopecon-bridge/dopecon_bridge/routes.py` is the bridge runtime surface, and `TRUTH_GAPS.md` explicitly warns against treating bridge surfaces as canonical authority. ADHD Engine integrations call into bridge clients or bridge-side integrations; they do not own bridge routing or bridge truth.

## 4. Key Surfaces

- Canonical runtime entrypoint:
  `services/adhd_engine/main.py` is the strongest runtime authority in this checkout.

- Canonical stdio MCP wrapper:
  `services/adhd_engine/mcp_stdio.py` imports `mcp` from `services.adhd_engine.main` and runs it with `transport="stdio"`.

- Active HTTP/container port:
  `8095` is the internal runtime port from `services/adhd_engine/config.py`, `docker/compose.core.yml`, and `services/registry.yaml`.
  `3025` is the exposed host port in `docker/compose.core.yml` and `services/registry.yaml`.

- Runtime transport surfaces:
  - HTTP root/info-style surface: `/` in `services/adhd_engine/main.py`
  - Health surface: `/health` in `services/adhd_engine/main.py`
  - Metrics surface: `/metrics` in `services/adhd_engine/main.py` and `/api/v1/metrics` in `services/adhd_engine/api/routes.py`
  - API surface prefix: `/api/v1`
  - MCP HTTP mount: `/mcp`
  - WebSocket surface: `/api/v1/ws/stream` in `services/adhd_engine/api/routes.py`
  - stdio MCP surface: `services/adhd_engine/mcp_stdio.py`

- API route surfaces:
  Core route families directly observed in `services/adhd_engine/api/routes.py` include:
  - assessment and recommendations: `/assess-task`, `/recommend-break`, `/break-recommendation`, `/predict`
  - state reads: `/energy-level/{user_id}`, `/attention-state/{user_id}`, `/cognitive-load/{user_id}`, `/flow-state/{user_id}`, `/session-time/{user_id}`, `/breaks/{user_id}`, `/statusline/{user_id}`, `/state`
  - profile/customization/trust: `/user-profile`, `/override-prediction`, `/customization-settings/{user_id}`, `/prediction-feedback/{user_id}`, `/trust-metrics/{user_id}`, `/trust-visualization/{user_id}`, `/automation-level/{user_id}`
  - activity and hook support: `/activity/{user_id}`, `/log-intent`, `/save-context`, `/unfinished-work`, `/record-progress`, `/external-activity`, `/log-git-event`

- Event surfaces:
  - `services/adhd_engine/event_emitter.py` publishes to Redis stream `dopemux:events`
  - `services/adhd_engine/event_listener.py` subscribes to `dopemux:events` through consumer group `adhd-engine`
  - `services/adhd_engine/integration_bridge_connector.py` emits buffered cognitive-state and break-needed events into bridge-side integration code when available
  These are transport/integration surfaces. They are not proof that ADHD Engine owns the global event bus.

- Projection/integration surfaces:
  - `services/adhd_engine/bridge_integration.py` writes bridge custom data and ADHD progress entries through `DopeconBridgeClient`, with fallback to `ConPortSQLiteClient`
  - `services/dopecon-bridge/integrations/adhd_engine.py` is a bridge-side ADHD integration surface for buffered event emission
  - `services/adhd_engine/core/task_orchestrator_client.py` is an outbound client to task-orchestrator
  - `ui-dashboard-backend/adhd-client.py` is a client/smoke-style consumer of ADHD Engine HTTP APIs

- Storage/state surfaces:
  - Redis-backed profile/state loading in `services/adhd_engine/core/engine.py`
  - in-process dictionaries and rolling buffers in `services/adhd_engine/core/engine.py` and `services/adhd_engine/api/routes.py`
  - bridge/custom-data and fallback SQLite projection path in `services/adhd_engine/bridge_integration.py`
  - context snapshots under `workspace_id/.context_snapshots` via `ContextPreserver` initialization in `services/adhd_engine/core/engine.py`
  These surfaces are mixed. The repo does not prove one unified durable ADHD-state store.

- Drifted or secondary surfaces:
  - `src/dopemux/adhd/` is a dopemux-side ADHD utility family, not the ADHD Engine runtime
  - `src/dopemux/adhd/context_manager.py` is a local SQLite context-preservation utility under `.dopemux/context.db`, not the canonical ADHD Engine service runtime
  - `services/adhd-engine` is a naming duplicate family called out in `TRUTH_GAPS.md`; `TRUTH_CANONICALS.md` recommends `services/adhd_engine` as canonical

## 5. System Boundaries

- dopemux
  ADHD Engine receives operator-local hook traffic and service consumption from dopemux-adjacent flows, but the inspected runtime does not prove `dopemux` as a required caller for all ADHD routes.
  ADHD Engine emits HTTP/MCP/WebSocket responses and ADHD-support state to its consumers.
  ADHD Engine does not control operator CLI policy, startup orchestration, or overall control-plane authority, which remain with `dopemux`.

- task-orchestrator
  ADHD Engine sends decomposition/coordination requests through `services/adhd_engine/core/task_orchestrator_client.py`.
  ADHD Engine may provide ADHD state to decomposition helpers and task-enablement logic.
  ADHD Engine does not control workflow legality, canonical task decomposition persistence, Leantime sync, or PM workflow authority.

- ConPort
  ADHD Engine reads or projects selected data through bridge/custom-data helpers and fallback ConPort-local SQLite access.
  ADHD Engine can store ADHD-adjacent progress/custom-data-like records, breadcrumbs, and intent/context traces into bridge/ConPort-adjacent paths.
  ADHD Engine does not control ConPort schema authority, structured decision authority, canonical progress authority, or ConPort retrieval/query semantics.

- dope-memory
  No inspected ADHD Engine runtime path proved dope-memory as its canonical backing store.
  ADHD Engine may overlap with memory-related support concepts such as breadcrumbs and context preservation, but those are not proof of dope-memory authority transfer.
  ADHD Engine does not control chronicle storage, recap, replay, or historical evidence authority.

- dope-context
  No direct inspected runtime call from ADHD Engine into dope-context was proven in the core runtime files inspected for this document.
  ADHD Engine may preserve context snapshots or context hints, but it does not control retrieval indexing, search ranking, or code/docs truth.

- dopecon-bridge
  ADHD Engine writes projected custom data and ADHD progress entries through a bridge client in `services/adhd_engine/bridge_integration.py`.
  Bridge-side code in `services/dopecon-bridge/integrations/adhd_engine.py` can buffer and publish cognitive-state and break/overload events.
  ADHD Engine does not control bridge routing policy, bridge health aggregation, bridge PM routing, or bridge authority claims.

- UI/dashboard surfaces
  `ui-dashboard-backend/adhd-client.py` consumes ADHD Engine endpoints such as `/api/v1/assess-task` and `/api/v1/activity/{USER_ID}`.
  `ui-dashboard-backend/main.py` runs a backend on port `3001`, but the inspected file does not itself prove a canonical ADHD dashboard contract beyond being an adjacent consumer runtime.
  ADHD Engine serves data to dashboard/backend consumers; it does not control the dashboard service.

## 6. Authority Model

- Canonical
  - the active HTTP/MCP runtime in `services/adhd_engine/main.py`
  - in-process current ADHD/operator-support state held by the running engine in `services/adhd_engine/core/engine.py`
  - ADHD-support assessments and recommendations produced by the engine and detector stack
  - ADHD Engine's own event-emission behavior from `services/adhd_engine/event_emitter.py` when that code path is used

- Derived
  - projected custom-data and ADHD progress entries written through `services/adhd_engine/bridge_integration.py`
  - breadcrumbs, context saves, and support records mirrored into bridge/custom-data paths by `WorkingMemorySupport` and related helpers
  - WebSocket status streams and statusline outputs from route handlers
  - dashboard/backend views that consume ADHD Engine APIs

- Operational
  - compose and registry wiring in `compose.yml`, `docker/compose.core.yml`, and `services/registry.yaml`
  - stdio MCP launch in `services/adhd_engine/mcp_stdio.py`
  - hook-facing routes in `services/adhd_engine/api/routes.py`
  - bridge-side event buffering and emission in `services/dopecon-bridge/integrations/adhd_engine.py`

- Unknown
  - one canonical durable store for historical ADHD state is not proven
  - full ownership of bridge-projected custom-data records is not proven as ADHD Engine authority once written downstream
  - event-listener runtime ownership is conditional because `services/adhd_engine/main.py` only starts it if `engine.event_bus` exists, and the inspected engine initialization does not clearly establish that attribute
  - repo-wide authority for context-preservation duties remains split across `services/adhd_engine/*`, `src/dopemux/adhd/*`, and memory-adjacent systems

Rule: ADHD Engine is authoritative for its running service state and recommendation logic. It is not authoritative for PM, memory, retrieval, bridge routing, or downstream structured records merely because it can emit or project data into those systems.

## 7. Known Drift / Issues

- Multiple ADHD/context state holders exist.
  Evidence: `services/adhd_engine/core/engine.py` holds runtime state in-memory and via Redis-backed loading; `services/adhd_engine/bridge_integration.py` can project to bridge/custom-data or fallback SQLite; `src/dopemux/adhd/context_manager.py` separately stores context snapshots in `.dopemux/context.db`.

- Event wiring is split and partly conditional.
  Evidence: `services/adhd_engine/event_emitter.py` uses Redis streams directly; `services/dopecon-bridge/integrations/adhd_engine.py` defines a separate bridge-side emission model; `services/adhd_engine/main.py` only starts `ADHDEventListener` if `engine.event_bus` exists, but the inspected `services/adhd_engine/core/engine.py` initialization does not clearly set `self.event_bus`.

- API surface breadth exceeds the narrow six-endpoint description in `main.py`.
  Evidence: `services/adhd_engine/main.py` docstring says "6 API endpoints (/api/v1/*) + 2 utility endpoints", while `services/adhd_engine/api/routes.py` exposes many more routes, including WebSocket, trust/customization, hook, metrics, and state endpoints.

- Port/config drift exists around adjacent callers.
  Evidence: ADHD Engine runtime uses internal `8095` and host `3025` in `docker/compose.core.yml` and `services/registry.yaml`, while `docs/03-reference/systems/task-orchestrator/SYSTEM_TaskOrchestrator.md` cites `services/task-orchestrator/app/core/coordinator.py` checking ADHD health at `http://localhost:8080/health`.

- ConPort URL default in ADHD Engine config conflicts with dedicated ConPort docs.
  Evidence: `services/adhd_engine/config.py` defaults `conport_url` to `http://localhost:3010`, while `docs/03-reference/systems/conport/SYSTEM_ConPort.md` and compose/registry surfaces place ConPort HTTP on `3004` and dope-context on `3010`.

- Hook/state routes can be mistaken for authoritative durable storage.
  Evidence: `/state`, `/log-intent`, `/save-context`, `/record-progress`, and `/log-git-event` in `services/adhd_engine/api/routes.py` write to rolling in-memory buffers or best-effort downstream projections, not a proven canonical durable ADHD ledger.

- Duplicate ADHD family naming remains in the repo.
  Evidence: `TRUTH_GAPS.md` calls out `services/adhd_engine` vs `services/adhd-engine`. `TRUTH_CANONICALS.md` recommends `services/adhd_engine` as the runtime authority.

- dopemux-side ADHD utilities overlap conceptually with the service.
  Evidence: `src/dopemux/adhd/` contains ADHD/task/context utilities such as `context_manager.py`, `attention_monitor.py`, and `workflow_manager.py`, but these are not the same as the FastAPI ADHD Engine runtime. This overlap can mislead documentation into inventing a single ADHD subsystem authority.

- Dashboard/backend assumptions are only partially proven.
  Evidence: `ui-dashboard-backend/adhd-client.py` assumes ADHD Engine HTTP APIs and API-key auth, but the inspected `ui-dashboard-backend/main.py` alone does not prove the full dashboard/backend contract or version alignment with the current ADHD Engine route set.

## 8. Working Rules

- Trust `services/adhd_engine/main.py`, `services/adhd_engine/core/engine.py`, `services/adhd_engine/api/routes.py`, and `services/adhd_engine/mcp_stdio.py` before older ADHD prose.

- Treat ADHD Engine as an operator-support and cognitive-state service only.
  Do not upgrade it into PM authority, memory authority, retrieval authority, or bridge authority without new runtime evidence.

- Treat current service state and generated recommendations as ADHD Engine-owned only while they are in its runtime surfaces.
  Once records are projected into bridge/custom-data or other systems, re-evaluate authority based on the destination system.

- Do not treat `/state`, hook buffers, WebSocket messages, or dashboard views as proof of durable canonical history.

- Do not treat bridge-projected custom data, ADHD progress entries, or ConPort-adjacent records as proving that ADHD Engine owns those stores.

- Preserve `UNKNOWN` where the repo does not prove a single durable ADHD-state store, a guaranteed event-bus runtime, or a single canonical context-preservation subsystem.

- Keep ADHD Engine, dope-memory, ConPort, dope-context, task-orchestrator, dopemux, and dopecon-bridge separate in documentation and debugging.
  If a flow crosses systems, identify the writer, transport, and destination authority explicitly instead of collapsing them into one "cognitive core".
