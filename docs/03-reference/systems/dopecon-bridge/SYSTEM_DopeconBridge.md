# SYSTEM_DopeconBridge

## 1. Purpose

DopeconBridge is the active adapter/proxy runtime that sits between callers and selected upstream services. In the inspected runtime it is the FastAPI app in `services/dopecon-bridge/main.py` backed by the modular routers in `services/dopecon-bridge/dopecon_bridge/routes.py`.

Its canonical authority slice is narrow:
- authenticated bridge routing behavior
- bridge-local event publication/subscription transport
- adapter policy for safe PM routing and fail-closed rejection of non-canonical workflow/task mutations
- compatibility proxy surfaces that normalize requests and responses around ConPort and selected MCP-style upstreams

It is not canonical task, workflow, decision, or progress authority. The active route module states this directly in its header docstring.

## 2. Core Responsibilities

- Serves the active DopeconBridge HTTP runtime.
  Evidence: `services/dopecon-bridge/main.py` constructs `FastAPI(...)`, configures CORS, initializes DB/cache in lifespan, and includes all routers returned by `get_all_routers()`.

- Provides authenticated bridge and token surfaces.
  Evidence: `services/dopecon-bridge/dopecon_bridge/routes.py` exposes `/auth/token` and `/auth/refresh`, using bridge auth helpers from `dopecon_bridge.auth`.

- Publishes and serves shared event-bus traffic.
  Evidence: `services/dopecon-bridge/dopecon_bridge/routes.py` exposes `/events`, `/events/stream`, `/events/history`, convenience event endpoints, and stream-info lookup. `services/dopecon-bridge/dopecon_bridge/event_bus.py` implements the Redis Streams wrapper used for publish/subscribe on streams such as `dopemux:events`.

- Routes only adapter-safe PM operations to Leantime-bridge and fails closed on workflow-significant mutations.
  Evidence: `services/dopecon-bridge/dopecon_bridge/routes.py` defines `SAFE_PM_ROUTE_OPERATIONS`, `WORKFLOW_SIGNIFICANT_OPERATIONS`, `_is_workflow_significant_pm_mutation(...)`, and `/route/pm`. The route rejects workflow-significant operations with `409` and only forwards safe operations through `mcp_client.call_tool("leantime-bridge", ...)`.

- Proxies ConPort-backed structured surfaces and normalizes their responses.
  Evidence: `services/dopecon-bridge/dopecon_bridge/routes.py` exposes `/kg/custom_data`, `/kg/decisions`, `/kg/progress`, `/ddg/decisions`, and `/ddg/search`, all backed by `conport_client` calls and normalization helpers such as `_normalize_decision_list(...)` and `_normalize_progress_list(...)`.

- Aggregates bridge-adjacent service health.
  Evidence: `/health` in `services/dopecon-bridge/dopecon_bridge/routes.py` calls `mcp_client.health_check_all()` and `conport_client.health_check()`.

- Maintains bridge-side HTTP client adapters for upstream services.
  Evidence: `services/dopecon-bridge/dopecon_bridge/clients.py` defines `MCPClientManager` for `task-orchestrator` and `leantime-bridge` tool calls and `ConPortClient` for direct ConPort REST calls.

## 3. Non-Responsibilities

- DopeconBridge does not own canonical task authority.
  Evidence: the header of `services/dopecon-bridge/dopecon_bridge/routes.py` states the bridge must not act as canonical task authority. `/tasks/parse-prd`, `/tasks/next/{project_id}`, and `/tasks/{task_id}/status` all fail closed rather than acting as authoritative task mutation surfaces.

- DopeconBridge does not own workflow authority or workflow legality.
  Evidence: `/route/pm` blocks workflow-significant mutations and explicitly says such mutations require Task Orchestrator adjudication before any Leantime reflection.

- DopeconBridge does not own decision or progress authority.
  Evidence: `/kg/decisions` and `/kg/progress` are explicit proxies to `conport_client.log_decision(...)` and `conport_client.log_progress(...)`, and the route responses are labeled with `"source": "conport"`.

- DopeconBridge does not own PM metadata authority.
  Evidence: `/route/pm` forwards only adapter-safe PM operations to `leantime-bridge`. It does not implement a bridge-local PM store.

- DopeconBridge does not own chronicle or memory authority.
  Evidence: no inspected bridge runtime file implements dope-memory ledger storage or chronicle operations. Memory-plane docs and truth artifacts assign that authority elsewhere.

- DopeconBridge does not own retrieval truth.
  Evidence: the inspected bridge runtime proxies ConPort and MCP-style upstreams; it does not implement dope-context indexing or retrieval authority.

## 4. Key Surfaces

- Canonical runtime entrypoint:
  `services/dopecon-bridge/main.py`

- Canonical route authority:
  `services/dopecon-bridge/dopecon_bridge/routes.py`

- Upstream client surfaces:
  `services/dopecon-bridge/dopecon_bridge/clients.py`

- Event transport surface:
  `services/dopecon-bridge/dopecon_bridge/event_bus.py`

- Active port:
  `3016` is the current bridge port in `docker/compose.core.yml`, `compose.yml`, and `services/registry.yaml`.
  `services/dopecon-bridge/dopecon_bridge/config.py` also derives `PORT_BASE + 16`, defaulting to `3016`.

- Primary APIs:
  - health/info: `/health`, `/`
  - auth: `/auth/token`, `/auth/refresh`
  - events: `/events`, `/events/stream`, `/events/history`, `/events/{stream}`, and convenience event routes
  - PM routing: `/route/pm`
  - blocked task compatibility routes: `/tasks/parse-prd`, `/tasks/next/{project_id}`, `/tasks/{task_id}/status`
  - ConPort proxy: `/kg/custom_data`, `/kg/decisions`, `/kg/progress`
  - decision-graph compatibility proxy: `/ddg/decisions`, `/ddg/search`

- Storage/state surfaces:
  - Redis Streams through `EventBus`
  - bridge-local DB/cache initialization in `main.py`
  - no repo-proven canonical bridge-owned PM/decision/progress store in the inspected runtime

## 5. System Boundaries

- task-orchestrator
  DopeconBridge calls Task Orchestrator health through `MCPClientManager.health_check_all()`.
  Bridge policy explicitly defers workflow-significant PM mutations to Task Orchestrator.
  DopeconBridge does not control Task Orchestrator workflow logic or runtime state.

- leantime-bridge
  DopeconBridge routes safe PM operations to `leantime-bridge` through `MCPClientManager.call_tool(...)` and normalizes the result.
  DopeconBridge does not control Leantime metadata truth or bridge-safe tool semantics upstream.

- ConPort
  DopeconBridge proxies decision/progress/custom-data reads and writes through `ConPortClient`.
  It emits normalized responses labeled `"source": "conport"` and publishes some bridge-side events after successful writes.
  It does not control ConPort schema or canonical structured-memory authority.

- dope-memory
  No direct canonical dope-memory write path was proven in the active bridge runtime inspected for this document.
  DopeconBridge does not control chronicle storage or dope-memory truth.

- ADHD Engine
  Bridge-side ADHD integrations exist in `services/dopecon-bridge/integrations/adhd_engine.py` for buffered state/overload/break events.
  That integration consumes ADHD-originated signals and publishes bridge-side events.
  DopeconBridge does not control ADHD Engine runtime state or recommendation logic.

- dopemux
  DopeconBridge serves as an operational HTTP dependency for dopemux-side adapters and other services.
  It does not control the operator CLI or become the control plane merely because it is widely called.

## 6. Authority Model

- Canonical
  - bridge-local routing policy in `services/dopecon-bridge/dopecon_bridge/routes.py`
  - bridge-local event transport behavior implemented in `services/dopecon-bridge/dopecon_bridge/event_bus.py`
  - bridge-local authentication/runtime wiring in `services/dopecon-bridge/main.py` and `dopecon_bridge/auth.py`

- Derived
  - normalized response bodies returned from upstream ConPort and leantime-bridge calls
  - compatibility `/ddg/*` views over ConPort decisions/search
  - aggregated health responses over upstream services

- Operational
  - `/route/pm` forwarding into leantime-bridge
  - `/kg/*` forwarding into ConPort
  - `/events/*` Redis-stream transport
  - bridge-side DB/cache initialization and health aggregation

- Unknown
  - the exact canonical role of the initialized bridge database beyond operational runtime support is not proven in the inspected route/client files
  - repo-wide exclusivity of bridge as the only proxy path is not proven

Rule: DopeconBridge is authoritative for its own adapter policy and transport behavior, not for the domain truth of the systems it proxies.

## 7. Known Drift / Issues

- The bridge exposes broad PM, KG, DDG, and event surfaces that can be mistaken for authority.
  Evidence: `services/dopecon-bridge/dopecon_bridge/routes.py` exposes `/route/pm`, `/kg/*`, `/ddg/*`, and `/events/*`, but its own module header says it must not act as canonical task, workflow, decision, or progress authority.

- Several legacy task-shaped routes now fail closed.
  Evidence: `/tasks/parse-prd`, `/tasks/next/{project_id}`, and `/tasks/{task_id}/status` all return explicit policy blocks instead of performing local task authority.

- The bridge both proxies ConPort writes and emits follow-up events, which can blur source ownership.
  Evidence: `/kg/decisions` and `/kg/progress` proxy writes into ConPort, then publish `decision.logged` and `progress.updated` events with `source="conport"`. The write authority is still upstream ConPort, not the bridge.

- Bridge health is an aggregate operational view, not authoritative upstream status.
  Evidence: `/health` composes `task-orchestrator`, `leantime-bridge`, and `conport` checks rather than proving bridge-local ownership of those services.

- Client URL defaults are environment-derived and may drift from other docs/config if not aligned.
  Evidence: `services/dopecon-bridge/dopecon_bridge/config.py` derives upstream URLs from env/default container names, while other system docs and compose files define their own runtime truths.

## 8. Working Rules

- Trust `services/dopecon-bridge/dopecon_bridge/routes.py` first when classifying bridge authority.

- Treat the bridge as adapter/proxy glue only.
  If a route returns upstream data, identify the upstream canonical writer before assigning truth.

- Do not document `/kg/*`, `/ddg/*`, or `/route/pm` as canonical domain stores.

- Treat bridge-local event publication as transport behavior, not as ownership of the event payload's domain truth.

- Preserve the fail-closed task/workflow blocks in documentation.
  Those rejections are part of the bridge's real runtime contract.

- Preserve `UNKNOWN` where the bridge database/cache role is not proven beyond operational support.
