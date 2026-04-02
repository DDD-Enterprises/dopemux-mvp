### 1. Purpose

ConPort is the active structured context service in this repository: the runtime under `docker/mcp-servers-source/conport/` persists workspace context, decision records, progress entries, and generic custom data in PostgreSQL, serves those records over HTTP and JSON-RPC from `enhanced_server.py`, and exposes an MCP-facing proxy surface from `server.py`. Its canonical authority slice is limited to the structured decision, progress, context, custom-data, and relationship-query surfaces that are actually implemented in that runtime. It is not global memory authority, it is not the PM authority for the full system, and it does not own chronicle history, workflow legality, or dope-context retrieval. Evidence: `repo-truth-pack/conport/EXECUTIVE_SUMMARY.md`, `repo-truth-pack/conport/DRIFT_REPORT.md`, `docker/mcp-servers-source/conport/enhanced_server.py`, `docker/mcp-servers-source/conport/schema.sql`, `docker/mcp-servers-source/conport/server.py`.

### 1.1 Runtime Reality

- The deployed/container runtime points at the Docker-packaged ConPort service under `docker/mcp-servers/conport`, which copies its active implementation from `docker/mcp-servers-source/conport`.
- The primary HTTP API surface is `3004`.
- The MCP SSE surface is `3005`.
- The info server surface is `4004`.

### 1.2 Intended / Historical

- The repository also contains `src/conport/memory_server.py`, which is a separate active-looking ConPort surface with its own MCP/runtime implementation.
- This checkout does not prove that `src/conport/memory_server.py` is the deployed authority over the Docker ConPort runtime.

### 1.3 Ports

- Primary HTTP API: `3004`
- MCP SSE / stdio-facing proxy runtime: `3005`
- Info server: `4004`
- Alternate / unclear authority surface: `src/conport/memory_server.py` (not proven as deployed primary runtime)

### 2. Core Responsibilities

- Structured decision storage and retrieval. `enhanced_server.py` implements `POST /api/decisions` and `GET /api/decisions`, backed by the `decisions` table in `schema.sql`. This is the clearest canonical ConPort slice in the current runtime.
- Structured progress representation and mutation. `enhanced_server.py` implements `POST /api/progress`, `GET /api/progress`, `PUT /api/progress/{progress_id}`, plus instance fork/promote endpoints. This proves ConPort owns a mutable progress representation, not an append-only chronicle.
- Workspace context storage and retrieval. `enhanced_server.py` implements `GET /api/context/{workspace_id}` and `POST /api/context/{workspace_id}` against `workspace_contexts`. This is an active runtime surface.
- Custom data storage. `enhanced_server.py` implements `POST /api/custom_data`, `GET /api/custom_data`, and `DELETE /api/custom_data` against `custom_data`. This is a mutable generic key/value surface, not a universal authority claim.
- Relationship and cross-workspace query surfaces, but only where implemented as reads. `enhanced_server.py` exposes `GET /api/workspace-relationships` and `GET /api/workspace-summary`, and `schema.sql` defines `entity_relationships`. `repo-truth-pack/conport/DRIFT_REPORT.md` states there is no ConPort write API for `entity_relationships`, so the runtime proves relationship traversal/query capability more clearly than canonical relationship creation authority.
- Callable runtime and API surfaces. `start_with_info.sh` starts `enhanced_server.py` on `3004`, `server.py sse` on `3005`, and `info_server.py` on `4004`. `server.py` and `conport_mcp_stdio.py` are thin MCP-facing delegates to the HTTP runtime, not separate stores.

### 3. Non-Responsibilities

- Canonical PM metadata authority. Repo PM write code keeps PM entity updates on Leantime and workflow transitions on task-orchestrator; ConPort is only one PM-plane slice for context/decision/progress logging.
- Workflow transition authority. ConPort progress status changes exist, but repo PM boundary code assigns workflow legality and canonical transitions to task-orchestrator, not ConPort.
- Chronicle or raw event history authority. ConPort publishes best-effort events and caches query results, but it is not the dope-memory chronicle ledger and does not prove append-only event authority.
- dope-context retrieval or indexing authority. ConPort may be queried or mirrored into retrieval flows, but the repo does not show it owning code/docs retrieval, semantic indexing, or search authority for dope-context.
- dope-memory chronicle authority. ConPort is separate from dope-memory and does not replace the chronicle ledger.
- Bridge or proxy transport authority. `dopecon-bridge` proxies some ConPort-compatible routes, but the bridge states it is an adapter/proxy only and must not act as canonical decision or progress authority.
- Universal memory authority. The runtime owns its PostgreSQL tables and exposed APIs only. It does not prove sole ownership of all decisions, progress, or memory across the repository.

### 4. Key Surfaces

- Canonical runtime entrypoint. `docker/mcp-servers-source/conport/enhanced_server.py` is the primary runtime and canonical API surface. `start_with_info.sh` starts it on port `3004`.
- Preferred canonical integration surface. For service-to-service integration, the repo-truth pack and runtime align on HTTP REST at `http://localhost:3004/api/*` and JSON-RPC at `POST http://localhost:3004/mcp`. This is the surface current adapters ultimately target when they are using real runtime paths.
- REST/HTTP surfaces. `enhanced_server.py` exposes context, decisions, progress, search, unified-search, workspace-relationships, workspace-summary, custom-data, health, metrics, and instance-management routes. These are the direct operator/runtime surfaces.
- JSON-RPC surface. `enhanced_server.py` exposes `/mcp` with `conport_*` methods. This is callable and partially discoverable. `repo-truth-pack/conport/DRIFT_REPORT.md` proves three instance-management tools are callable but omitted from `tools/list`.
- FastMCP surfaces. `docker/mcp-servers-source/conport/server.py` exposes 13 unprefixed MCP tools over SSE on `3005/mcp` and stdio. `conport_mcp_stdio.py` exposes the same tool set for stdio/admin-style usage. These tools proxy to `CONPORT_URL` on port `3004`.
- Proxy and transport surfaces. `services/dopecon-bridge/dopecon_bridge/routes.py` exposes `/kg/*` and `/ddg/*` compatibility routes backed by its own ConPort client. These are transport/adaptation surfaces, not canonical ConPort authority.
- Custom-data surface. `POST/GET/DELETE /api/custom_data` is an active mutable surface backed by `custom_data`. Operators should treat it as a generic structured store with narrow authority over those stored values only.
- Derived and mutable surfaces. Redis-backed caches, active-work views, recent-activity views, and workspace-summary/relationship traversal outputs are derived query surfaces. They are useful runtime outputs, but they are not stronger than the underlying tables and query code.

### 5. System Boundaries

- dopemux. `src/dopemux/pm/reads.py` treats ConPort as canonical for project context and decision-context reads, and `src/dopemux/pm/writes.py` routes `pm_log_progress` to ConPort as the primary write for context/decision logging. `src/dopemux/pm/adapters/conport.py` also uses bridge-backed `/kg/custom_data` compatibility paths. ConPort receives structured writes and reads from dopemux. It emits structured decision/progress/context/custom-data responses. It does not control dopemux PM policy, PM entity truth, or workflow legality.
- dope-memory. Repo PM writes mirror ConPort context/decision logging into dope-memory chronicle receipts, which means ConPort can be an upstream structured source for some memory mirroring. It does not control dope-memory chronicle storage, recap, replay, or temporal authority.
- task-orchestrator. `services/task-orchestrator/app/adapters/conport_adapter.py` transforms orchestration tasks into ConPort progress entries and reads ConPort context/decision/progress surfaces for enrichment. ConPort receives structured task/progress-like data and serves back context, decisions, and progress records. It does not control task-orchestrator workflow transitions, legality gates, or orchestration ownership.
- dope-context. Repo code includes integrations that read from or mirror ConPort into embedding/retrieval flows, but ConPort only emits structured records and custom data for those consumers. It does not control dope-context indexing, retrieval ranking, or code/doc authority.
- dopecon-bridge. `integration_bridge_client.py` in the ConPort runtime publishes best-effort `decision_logged` and `progress_updated` events outward to the bridge. The bridge also proxies `/kg/*` and `/ddg/*` requests back into ConPort through its own client. ConPort emits events and serves HTTP APIs; it does not control bridge auth, proxy policy, or transport normalization.

### 6. Authority Model

- Canonical. Decisions, workspace context, progress entries, and custom-data records written through `enhanced_server.py` into ConPort's PostgreSQL schema are canonical for those ConPort-owned structured domains.
- Canonical, but narrow. Relationship-query surfaces are canonical only to the extent the runtime can read and traverse relationship data through `entity_relationships` and `unified_queries.py`. Repo truth does not prove ConPort as the canonical writer for all relationship data because no relationship write API is exposed.
- Operational. `server.py` and `conport_mcp_stdio.py` are operational transport layers for MCP consumption. They are active and important, but they delegate to the HTTP runtime rather than creating separate truth.
- Operational. DopeconBridge event publishing and proxy calls are operational integration paths around ConPort, not ConPort's authority boundary.
- Derived. `recent_activity`, `active_work`, `workspace_summary`, search results, Redis caches, and token-truncated list responses are derived or presentation-oriented outputs.
- Unknown. Repo-wide exclusivity for decisions/progress is not proven. `repo-truth-pack/conport/DRIFT_REPORT.md` explicitly says sole-authority claims are not enforced.
- Unknown. Universal authority for relationship creation is unresolved because the schema and traversal reads exist, but the runtime does not expose a corresponding relationship write API.
- Rule. Mutable surfaces, especially `progress_entries`, `workspace_contexts`, and `custom_data`, do not imply ConPort is universal system truth; they only prove ConPort is authoritative for what is actually stored and served there.

### 7. Known Drift / Issues

- Docs overclaim sole authority. `repo-truth-pack/conport/DRIFT_REPORT.md` shows the "if it is not in ConPort it did not formally happen" invariant is not enforced by the runtime.
- Mutable reality versus stronger memory claims. The same drift report proves `progress_entries` and `workspace_contexts` are mutable and `custom_data` supports delete, which conflicts with stronger append-only or ledger-style claims.
- Relationship authority is weaker than some graph language suggests. `schema.sql` defines `entity_relationships`, and `enhanced_server.py` exposes relationship traversal reads, but `repo-truth-pack/conport/DRIFT_REPORT.md` states there is no ConPort write API for `entity_relationships`.
- Transport and proxy ambiguity. The active source lives in `docker/mcp-servers-source/conport`, while `compose.yml` points at `./docker/mcp-servers/conport`; the truth pack marks that build-context mismatch as drift. Operators should classify that as packaging drift, not a separate authority surface.
- Multiple runtime surfaces exist. `docker/mcp-servers-source/conport` is the strongest deployed/runtime evidence, while `src/conport/memory_server.py` is a separate active-looking alternate surface with unresolved canonicality.
- Prefixed versus unprefixed tool naming drift. FastMCP exposes unprefixed tools like `get_context`, while JSON-RPC exposes prefixed `conport_get_context` methods. The truth pack also records a payload mismatch for `log_decision` and a default-status mismatch for `log_progress`.
- Surface discoverability drift. `repo-truth-pack/conport/DRIFT_REPORT.md` proves JSON-RPC exposes callable instance-management tools that are omitted from `tools/list`, and `workspace_summary` exists on FastMCP/HTTP but not in JSON-RPC dispatch.
- Info and transport metadata drift. The truth pack records `info_server.py` advertising the wrong SSE URL and the Dockerfile omitting port `3005` from `EXPOSE`.

### 8. Working Rules

- Use ConPort for structured decision, progress, context, custom-data, and relationship-query questions only where those surfaces are actually implemented.
- Prefer `enhanced_server.py` on `3004` as the canonical runtime/API, and treat FastMCP and bridge routes as transport or compatibility layers unless runtime evidence proves otherwise.
- Do not treat ConPort as sole memory truth, sole PM truth, or chronicle truth.
- Do not collapse ConPort into dope-memory, dope-context, task-orchestrator, or dopecon-bridge because they integrate with it.
- Trace any answer back to the implemented runtime path or schema surface that actually serves it.
- Preserve `UNKNOWN` where relationship creation authority, repo-wide exclusivity, or cross-system canonical ownership is unresolved.
