---
id: TRUTH_SYSTEMS
title: Truth Systems
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: Truth Systems (reference) for dopemux documentation and developer workflows.
---
# TRUTH_SYSTEMS

Method:
- Only systems classified as Core Architectural Authority or Essential Operational Support are included here.
- `Observed` and `Inference` are separated inline.
- `Non-responsibilities` are only listed where repo truth supports them.

## `dopemux core`

- Purpose:
  - Primary CLI/runtime package for Dopemux.
- Responsibilities:
  - Exposes top-level CLI commands from `[LOCAL_PATH_REDACTED]`.
  - Hosts kernel integration, extractor command wiring, routing/provider config loading, and operator workflow commands.
- Non-responsibilities:
  - Not the canonical repo-truth extraction runtime for v5; that authority is delegated to `[LOCAL_PATH_REDACTED]`.
- Dependencies:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
- Inbound interfaces:
  - `dopemux` console script from `[LOCAL_PATH_REDACTED]`
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
  - Installs the pinned `dopetask` version from `[LOCAL_PATH_REDACTED]`.
  - Executes the external `dopetask` CLI.
- Non-responsibilities:
  - Does not contain Dopetask implementation itself.
  - `scripts/taskx` is not a distinct runner; it is a shim.
- Dependencies:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - repo-local virtualenv under `.dopetask_venv`
- Inbound interfaces:
  - `[LOCAL_PATH_REDACTED]`
  - direct shell execution of `[LOCAL_PATH_REDACTED]`
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
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - trajectory logic under `[LOCAL_PATH_REDACTED]`
- Inbound interfaces:
  - HTTP endpoints in `[LOCAL_PATH_REDACTED]`
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
  - No direct evidence that `[LOCAL_PATH_REDACTED]` is a runnable MCP server.
- Dependencies:
  - Local application logic under `[LOCAL_PATH_REDACTED]`
  - JWT/auth surfaces in the same service tree
- Inbound interfaces:
  - HTTP endpoints from `[LOCAL_PATH_REDACTED]`
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
  - Milvus manager and PostgreSQL manager in `[LOCAL_PATH_REDACTED]`
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
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
- Inbound interfaces:
  - FastMCP tools from `[LOCAL_PATH_REDACTED]`
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
  - `[LOCAL_PATH_REDACTED]` explicitly says this layer must no longer be used as runtime authority.
- Dependencies:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
- Inbound interfaces:
  - HTTP routes in `[LOCAL_PATH_REDACTED]`
  - stdio MCP entry in `[LOCAL_PATH_REDACTED]`
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
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - upstream `task-orchestrator`, `leantime-bridge`, and ConPort HTTP APIs
- Inbound interfaces:
  - HTTP routes declared in `[LOCAL_PATH_REDACTED]`
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
  - Exposes current operator workflow through `dopemux rte`; `dopemux upgrades` remains a legacy compatibility alias.
  - Provides doctor, preflight, coverage, status, routing, compare, and validation surfaces.
  - Ships hygiene scanning policies and tests for phase interaction.
- Non-responsibilities:
  - Legacy `PipelineRunner`/`dopemux truth` shortcut is not the same as the v5 extraction service.
  - Generated proof packs and truth docs are evidence artifacts, not source truth above runtime code/config/tests.
- Dependencies:
  - `[LOCAL_PATH_REDACTED]`
  - extractor tests under `[LOCAL_PATH_REDACTED]`
- Inbound interfaces:
  - canonical CLI execution via `dopemux rte` in `[LOCAL_PATH_REDACTED]`
  - legacy compatibility CLI execution via `dopemux upgrades`
  - advanced/debug direct execution of `run_extraction_v5.py`
  - deprecated/refusal `dopemux extractor`, `dopemux truth`, and hidden `dopemux extract truth-run` surfaces
- Outbound interfaces:
  - Writes extraction run artifacts under `[LOCAL_PATH_REDACTED]`
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
  - No evidence in this pass that the duplicate `[LOCAL_PATH_REDACTED]` path is canonical.
- Dependencies:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
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
  - Observed deployment path builds a Serena wrapper image from `[LOCAL_PATH_REDACTED]`.
  - Observed config aliases map `serena-v2`, `serena`, and `dopemux-serena`.
- Non-responsibilities:
  - No single repo path is proven canonical for Serena implementation and deployment at the same time.
- Dependencies:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
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
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
- Inbound interfaces:
  - Dopemux CLI/profile loading and external MCP clients
- Outbound interfaces:
  - Effective provider selection and MCP startup routing
- Role in overall dopemux development workflow:
  - Operational glue that determines which service surfaces are actually reachable.
