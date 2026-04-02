# TRUTH_SYSTEMS

Method:
- Only systems classified as Core Architectural Authority or Essential Operational Support are included here.
- `Observed` and `Inference` are separated inline.
- `Non-responsibilities` are only listed where repo truth supports them.

## `dopemux core`

- Purpose:
  - Primary CLI/runtime package for Dopemux.
- Responsibilities:
  - Exposes top-level CLI commands from `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py`.
  - Hosts kernel integration, extractor command wiring, routing/provider config loading, and operator workflow commands.
- Non-responsibilities:
  - Not the canonical repo-truth extraction runtime for v5; that authority is delegated to `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v5.py`.
- Dependencies:
  - `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extractor_commands.py`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/routing_config.py`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/profile_models.py`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/claude_config.py`
- Inbound interfaces:
  - `dopemux` console script from `/Users/hue/code/dopemux-mvp/pyproject.toml`
- Outbound interfaces:
  - Subprocess calls into scripts and extractor runners.
  - MCP/routing config generation and provider resolution.
- Role in overall dopemux development workflow:
  - Operator control plane and local command surface.

## `dopetask integration surface`

- Purpose:
  - Pinned task-runner bootstrap for development workflows driven from Dopemux.
- Responsibilities:
  - Validates repo marker files.
  - Creates and reuses `.dopetask_venv`.
  - Installs the pinned `dopetask` version from `/Users/hue/code/dopemux-mvp/.dopetask-pin`.
  - Executes the external `dopetask` CLI.
- Non-responsibilities:
  - Does not contain Dopetask implementation itself.
  - `scripts/taskx` is not a distinct runner; it is a shim.
- Dependencies:
  - `/Users/hue/code/dopemux-mvp/.dopetaskroot`
  - `/Users/hue/code/dopemux-mvp/.dopetask-pin`
  - repo-local virtualenv under `.dopetask_venv`
- Inbound interfaces:
  - `/Users/hue/code/dopemux-mvp/src/dopemux/commands/kernel_commands.py`
  - direct shell execution of `/Users/hue/code/dopemux-mvp/scripts/dopetask`
- Outbound interfaces:
  - `pip install` of pinned `dopetask`
  - exec of the `dopetask` binary
- Role in overall dopemux development workflow:
  - External task-management bridge used by `dopemux kernel`.

## `dope-memory`

- Purpose:
  - Durable repo/work-session memory service backed by a canonical SQLite chronicle ledger.
- Responsibilities:
  - Stores work-log entries and raw events.
  - Supports search, recap, issue marking, resolution linking, replay, correction, reflections, and trajectory queries via HTTP `/tools/*`.
  - Resolves canonical ledger location fail-closed using workspace root rules.
- Non-responsibilities:
  - Not the canonical PM status authority; PM metadata and workflow status authority is elsewhere.
- Dependencies:
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/canonical_ledger.py`
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/store.py`
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/schema.sql`
  - trajectory logic under `/Users/hue/code/dopemux-mvp/services/working-memory-assistant`
- Inbound interfaces:
  - HTTP endpoints in `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`
- Outbound interfaces:
  - SQLite ledger writes under `repo_root/.dopemux/chronicle.sqlite`
- Role in overall dopemux development workflow:
  - Evidence-preserving memory sink and retrieval surface for ongoing work.

## `working-memory-assistant`

- Purpose:
  - Snapshot/recovery and ADHD-adjacent memory support service.
- Responsibilities:
  - Exposes `/snapshot`, `/recover`, `/contexts/{user_id}`, `/preferences/{user_id}`, `/adhd-*`, `/stats/{user_id}`, and `/health`.
  - Provides a separate operational service from the canonical dope-memory HTTP surface.
- Non-responsibilities:
  - No direct evidence that it is the canonical durable dope-memory runtime.
  - No direct evidence that `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/mcp/server.py` is a runnable MCP server.
- Dependencies:
  - Local application logic under `/Users/hue/code/dopemux-mvp/services/working-memory-assistant`
  - JWT/auth surfaces in the same service tree
- Inbound interfaces:
  - HTTP endpoints from `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/main.py`
- Outbound interfaces:
  - `UNKNOWN` from this pass for all persistent writers used by this app surface.
- Role in overall dopemux development workflow:
  - Operational support for snapshot/recovery and ADHD/context continuity.

## `conport`

- Purpose:
  - Structured memory, semantic retrieval, and graph-link surface.
- Responsibilities:
  - Registers MCP tools `mem.upsert`, `mem.search`, `graph.link`, `graph.neighbors`.
  - In HTTP mode exposes `/health`, `/api/mem/search`, `/api/mem/upsert`, `/api/graph/link`, `/api/graph/neighbors`, `/sse`, and `/messages`.
  - Uses Milvus for vector retrieval and PostgreSQL for node/graph state.
- Non-responsibilities:
  - No evidence that `services/dope-query` is the same active runtime.
- Dependencies:
  - Milvus manager and PostgreSQL manager in `/Users/hue/code/dopemux-mvp/src/conport/memory_server.py`
- Inbound interfaces:
  - MCP stdio/SSE/HTTP surfaces in `memory_server.py`
- Outbound interfaces:
  - Milvus similarity search
  - PostgreSQL node and edge persistence
- Role in overall dopemux development workflow:
  - Structured truth and retrieval substrate consumed by bridge, ADHD, and PM logging paths.

## `dope-context`

- Purpose:
  - Code/document context indexing and deterministic hybrid retrieval.
- Responsibilities:
  - FastMCP server for workspace indexing, code search, docs indexing/search, hybrid search, autonomous indexing controls, and metrics.
  - Exposes health/info/bootstrap/status routes.
  - Contract tests assert schema compatibility.
  - Determinism tests assert stable hybrid ranking order.
- Non-responsibilities:
  - `mcp-proxy-config*` entries are not runtime authority.
- Dependencies:
  - `/Users/hue/code/dopemux-mvp/services/dope-context/contracts`
  - `/Users/hue/code/dopemux-mvp/services/dope-context/tests`
- Inbound interfaces:
  - FastMCP tools from `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`
  - HTTP routes `/health`, `/info`, `/autoindex/bootstrap`, `/autoindex/status`
- Outbound interfaces:
  - Search/index backends are present in service code, but exact storage backend was not fully traced in this pass.
- Role in overall dopemux development workflow:
  - Retrieval plane for code/docs context and deterministic search behavior.

## `task-orchestrator`

- Purpose:
  - Workflow coordination, PM write normalization, and cross-plane operations.
- Responsibilities:
  - Provides HTTP workflow APIs for ideas/epics/coordination.
  - Provides MCP tools for dependency analysis, batching, ADHD state access, sessions, decomposition, workflow status, and risk assessment.
  - Emits/broadcasts coordination events over WebSocket.
  - Persists workflow ideas/epics/audit through DopeconBridge custom data categories.
- Non-responsibilities:
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py` explicitly says this layer must no longer be used as runtime authority.
- Dependencies:
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_service.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/core/coordinator.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/mcp/__init__.py`
- Inbound interfaces:
  - HTTP routes in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`
  - stdio MCP entry in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/mcp_stdio.py`
- Outbound interfaces:
  - Async DopeconBridge client for custom data persistence.
  - PM canonical receipt flows.
  - WebSocket event broadcast.
- Role in overall dopemux development workflow:
  - Central orchestrator for workflow and multi-plane task state.

## `dopecon-bridge`

- Purpose:
  - Adapter/proxy layer across PM tools, ConPort, event bus, and compatibility surfaces.
- Responsibilities:
  - Authentication endpoints.
  - Event publication/stream/history.
  - PM routing under `/route/pm`.
  - ConPort proxy surfaces under `/kg/*`.
  - Compatibility decision graph endpoints under `/ddg/*`.
  - Health aggregation across upstream services.
- Non-responsibilities:
  - `routes.py` explicitly says it must not act as canonical task, workflow, decision, or progress authority.
- Dependencies:
  - `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/clients.py`
  - `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/event_bus.py`
  - upstream `task-orchestrator`, `leantime-bridge`, and ConPort HTTP APIs
- Inbound interfaces:
  - HTTP routes declared in `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/routes.py`
- Outbound interfaces:
  - HTTP POST to upstream MCP-style `/api/tools/{tool_name}` for selected services.
  - Direct HTTP calls to ConPort decision/progress/custom-data endpoints.
  - Redis event bus.
- Role in overall dopemux development workflow:
  - Coordination gateway and compatibility proxy between planes.

## `repo-truth-extractor`

- Purpose:
  - Canonical multi-phase repo-truth extraction and audit service.
- Responsibilities:
  - Executes extraction pipelines through `run_extraction_v5.py`.
  - Preserves v4 contract compatibility through `run_extraction_v4.py`.
  - Provides doctor, preflight, coverage, status, routing, compare, and validation surfaces.
  - Ships hygiene scanning policies and tests for phase interaction.
- Non-responsibilities:
  - Legacy `PipelineRunner` shortcut is not the same as the v5 extraction service.
- Dependencies:
  - `/Users/hue/code/dopemux-mvp/config/extraction_hygiene/authority_tiers.yaml`
  - extractor tests under `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/tests`
- Inbound interfaces:
  - CLI execution via `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extractor_commands.py`
  - direct execution of `run_extraction_v5.py`
- Outbound interfaces:
  - Writes extraction run artifacts under `/Users/hue/code/dopemux-mvp/extraction/repo-truth-extractor/v3/runs`
- Role in overall dopemux development workflow:
  - Canonical truth/audit pipeline for repository analysis work.

## `ADHD engine`

- Purpose:
  - Cognitive-state, workload, break recommendation, and context-state operational service.
- Responsibilities:
  - Exposes FastAPI health/root/metrics/background-service routes.
  - Exposes `/api/v1/*` endpoints for assessment, energy, attention, breaks, activity, patterns, complexity, prediction, statusline, context saving, unfinished work, progress recording, and git event logging.
  - Registers MCP tools including `get_cognitive_state` and `assess_task_complexity`.
- Non-responsibilities:
  - No evidence in this pass that the duplicate `/Users/hue/code/dopemux-mvp/services/adhd-engine` path is canonical.
- Dependencies:
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine/api/routes.py`
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine/core/activity_tracker.py`
  - ConPort progress client surfaces
- Inbound interfaces:
  - HTTP routes in `main.py` and `api/routes.py`
  - MCP tools in `main.py`
- Outbound interfaces:
  - ConPort progress retrieval and related support integrations
- Role in overall dopemux development workflow:
  - Cognitive and context support plane that can feed orchestration and operator state.

## `Serena surfaces`

- Purpose:
  - Code-intelligence/runtime-development assistance surface used through MCP/proxy integration.
- Responsibilities:
  - Observed deployment path builds a Serena wrapper image from `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/serena`.
  - Observed config aliases map `serena-v2`, `serena`, and `dopemux-serena`.
- Non-responsibilities:
  - No single repo path is proven canonical for Serena implementation and deployment at the same time.
- Dependencies:
  - `/Users/hue/code/dopemux-mvp/compose.yml`
  - `/Users/hue/code/dopemux-mvp/mcp-proxy-config*.{json,yaml}`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/claude_config.py`
- Inbound interfaces:
  - SSE/proxy surfaces on configured Serena port `3006`
- Outbound interfaces:
  - External Serena package/runtime via wrapper image
- Role in overall dopemux development workflow:
  - Optional but relevant code intelligence surface for MCP-enabled workflows.

## `MCP / routing / model-provider surfaces`

- Purpose:
  - Resolve effective provider/model/slot/fallback behavior and MCP launch topology.
- Responsibilities:
  - Validate routing files and aliases.
  - Generate LiteLLM-compatible provider configuration.
  - Map Claude/MCP server aliases for developer tooling.
  - Describe launch commands for MCP proxy clients.
- Non-responsibilities:
  - These files are not themselves the runtime implementation of ConPort, Serena, Dope-Context, or Task-Orchestrator.
- Dependencies:
  - `/Users/hue/code/dopemux-mvp/src/dopemux/routing_config.py`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/litellm_proxy.py`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/profile_models.py`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/claude_config.py`
  - `/Users/hue/code/dopemux-mvp/mcp-proxy-config.json`
  - `/Users/hue/code/dopemux-mvp/mcp-proxy-config.yaml`
  - `/Users/hue/code/dopemux-mvp/mcp-proxy-config.copilot.yaml`
- Inbound interfaces:
  - Dopemux CLI/profile loading and external MCP clients
- Outbound interfaces:
  - Effective provider selection and MCP startup routing
- Role in overall dopemux development workflow:
  - Operational glue that determines which service surfaces are actually reachable.
