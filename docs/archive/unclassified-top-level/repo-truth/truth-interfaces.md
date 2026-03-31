---
id: truth-interfaces
title: Truth Interfaces
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-31'
last_review: '2026-03-31'
next_review: '2026-06-29'
prelude: Truth Interfaces (explanation) for dopemux documentation and developer workflows.
---
# TRUTH_INTERFACES

Static inspection only. No runtime execution, no network calls, no destructive actions.

## Commands Used

- `rg --files ...`
- `rg -n ...`
- `sed -n ...`

## Scope Notes

- Fact means directly observed in repository files.
- Inference means derived from multiple repository signals but not proven by runtime execution.
- Unknown means static inspection did not establish the answer.

## 1. dopemux core

### Canonical entrypoints

- Fact: top-level CLI script is `dopemux = "dopemux.cli:main"` in `/Users/hue/code/dopemux-mvp/pyproject.toml`.
- Fact: module entrypoint `/Users/hue/code/dopemux-mvp/src/dopemux/__main__.py` calls `main()` from `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py`.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` is the main Click surface and registers the major groups.

### CLI surface

- Fact: observed command/group registrations in `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` include `workflow`, `trigger`, `memory`, `mcp`, `servers`, `extractor`, `upgrades`, `truth`, `launch`, `pr-merge`, and others.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/commands/upgrades_commands.py` defines the `upgrades` group.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extractor_commands.py` marks `dopemux extractor` as legacy and prints `use dopemux upgrades`.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` still exposes a direct `truth` command backed by `PipelineRunner` from `/Users/hue/code/dopemux-mvp/src/dopemux/extractor/runner.py`.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extract_commands.py` exposes `dopemux extract truth-run`, which directly locates and executes `services/repo-truth-extractor/run_extraction_v5.py`.

### Adapters/clients used by other systems

- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/conport/wire_project.py` writes project `.claude/claude_config.json` for the `conport` MCP server and installs a `post-checkout` hook that runs `dopemux wire-conport`.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/mcp/registry.py` and `/Users/hue/code/dopemux-mvp/src/dopemux/mcp/resolver.py` provide MCP registry loading and endpoint resolution.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/memory/capture_client.py` is the CLI/plugin capture adapter into the canonical chronicle ledger.

### Request/response schemas

- Fact: CLI surfaces are Click-based; request/response schemas are mostly plain option parsing, except where dopemux forwards to HTTP or subprocess entrypoints.

### Concrete execution path example: dopemux-driven workflow

1. Fact: user-facing command `dopemux workflow ideas add ...` is defined in `/Users/hue/code/dopemux-mvp/src/dopemux/commands/workflow_group_commands.py`.
2. Fact: that command calls `_workflow_request("POST", "/api/workflow/ideas", ...)` in `/Users/hue/code/dopemux-mvp/src/dopemux/commands/capture_group_commands.py`.
3. Fact: `_workflow_request` defaults to `DOPEMUX_WORKFLOW_API_URL` or `http://localhost:8000`.
4. Fact: active task-orchestrator FastAPI runtime is `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`, which mounts workflow routers.
5. Fact: workflow data models are defined in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/models/workflow.py`.

### Interface inconsistencies / duplicate entrypoints / dead paths

- Fact: `dopemux extractor` remains exposed but self-labels as legacy in `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extractor_commands.py`.
- Fact: `dopemux truth` and `dopemux extract truth-run` both target repo-truth extraction, but through different runners: `PipelineRunner` versus direct `run_extraction_v5.py`.
- Inference: `dopemux extract truth-run` is the more direct runtime path for current v5 extraction, while `dopemux truth` appears older and wrapper-oriented.

## 2. dopetask integration surface

### Canonical entrypoints

- Fact: `/Users/hue/code/dopemux-mvp/scripts/dopetask` is the workspace wrapper script.
- Fact: `/Users/hue/code/dopemux-mvp/.dopetask-pin` pins `dopetask` version `0.5.1`.
- Fact: `/Users/hue/code/dopemux-mvp/.dopetaskroot` exists and is checked by the wrapper.

### CLI surface

- Fact: the wrapper creates `.dopetask_venv`, installs the pinned package, then execs `dopetask`.
- Fact: the wrapper contains explicit handling for `dopetask doctor`.

### Adapters/clients used by other systems

- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux_pr_merge_specialist/dopetask_adapter.py` loads and normalizes task packets.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux_pr_merge_specialist/dopetask_packet_launcher.py` maps task packets to execution lanes and writes proof bundles.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux_pr_merge_specialist/dopetask_compatibility_mode.py` normalizes canonical and legacy manifest shapes.

### Schemas

- Fact: no single dopetask schema file was inspected here; the observed contract surface is the pinned wrapper plus PRMS adapters.

### Inconsistencies / drift

- Unknown: full dopetask command surface beyond the wrapper was not inspected inside the installed external package.

## 3. working-memory-assistant / dope-memory

### Canonical entrypoints

- Fact: `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py` says: `This is the canonical entry point for the Dope-Memory service.`
- Fact: `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/canonical_ledger.py` says all Dope-Memory write paths must resolve the single canonical ledger at `repo_root/.dopemux/chronicle.sqlite`.
- Fact: `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/store.py` says it is the `SQLite canonical storage for Dope-Memory`.

### CLI surface

- Fact: no dedicated top-level CLI for dope-memory was found beyond the HTTP server and the dopemux capture client.

### FastAPI routes / major endpoints

- Fact: `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py` exposes:
  - `/health`
  - `/`
  - `/tools/memory_search`
  - `/tools/memory_store`
  - `/tools/memory_recap`
  - `/tools/memory_mark_issue`
  - `/tools/memory_link_resolution`
  - `/tools/memory_replay_session`
  - `/tools/memory_correct`
  - `/tools/memory_generate_reflection`
  - `/tools/memory_reflections`
  - `/tools/memory_trajectory`

### MCP servers/tools

- Fact: `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py` defines inline tool handlers through `DopeMemoryMCPServer`.
- Fact: `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/mcp/server.py` defines a second `DopeMemoryMCPServer` implementation with overlapping `memory_search`, `memory_store`, and related methods.

### Adapters/clients used by other systems

- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/memory/capture_client.py` is the active dopemux-side writer into the chronicle ledger.
- Fact: `emit_capture_event()` in that file resolves repo root, capture mode, redacts payload via WMA redactor, deterministically computes `event_id`, initializes WMA SQLite schema/migrations, and inserts into `raw_activity_events`.

### Request/response schemas where discoverable

- Fact: request models such as `MemorySearchRequest` and `MemoryStoreRequest` are defined in `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`.
- Fact: the chronicle store shape is concrete in `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/schema.sql` plus accessors in `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/store.py`.

### Concrete execution path example: chronicle event capture / promotion / retrieval

1. Fact: dopemux capture path starts at `emit_capture_event()` in `/Users/hue/code/dopemux-mvp/src/dopemux/memory/capture_client.py`.
2. Fact: that function writes a redacted raw event into `.dopemux/chronicle.sqlite` table `raw_activity_events`.
3. Fact: promotion rules are defined in `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/promotion/promotion.py` by `PromotionEngine`, with canonical promotable types such as `decision.logged`, `task.completed`, `task.failed`, `task.blocked`, `error.encountered`, `workflow.phase_changed`, and `manual.memory_store`.
4. Fact: curated durable entries are inserted through `insert_work_log_entry()` and `insert_promoted_entry()` in `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/store.py`.
5. Fact: retrieval uses `search_work_log()` in `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/store.py`, surfaced over HTTP by `/tools/memory_search` in `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`.

### Interface inconsistencies / duplicate entrypoints / dead paths

- Fact: `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/main.py` exposes an older `Working Memory Assistant` API with routes like `/snapshot`, `/recover`, `/contexts/{user_id}`, `/preferences`, and `/adhd-*`.
- Fact: `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py` declares itself canonical.
- Inference: `services/working-memory-assistant/main.py` is a competing legacy runtime relative to canonical `dope_memory_main.py`.
- Fact: there are two `DopeMemoryMCPServer` implementations: one inline in `dope_memory_main.py`, one in `mcp/server.py`.

## 4. conport / dope-query

### Canonical entrypoints

- Fact: active ConPort project wiring in dopemux targets `conport-mcp` via `/Users/hue/code/dopemux-mvp/src/dopemux/conport/wire_project.py` and `/Users/hue/code/dopemux-mvp/scripts/mcp-wrappers/conport-wrapper.sh`.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/mcp/registry.yaml` lists `conport` as an MCP server with local command `uvx --from context-portal-mcp conport-mcp`.
- Fact: `/Users/hue/code/dopemux-mvp/docker/compose.core.yml` defines the `conport` container and ports.

### CLI surface

- Fact: no top-level dedicated `conport` CLI inside this repo was identified beyond wrappers and MCP/server config.

### FastAPI routes / major endpoints

- Fact: active ConPort REST is consumed through `/api/decisions`, `/api/search/{workspace_id}`, `/api/progress`, `/api/custom_data` by `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/clients.py`.
- Unknown: the active ConPort REST implementation file was not established from checked-in Python sources.

### MCP servers/tools

- Fact: `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/conport/server.py` exposes unprefixed tools such as `get_progress`, `update_progress`, `get_decisions`, `log_decision`, `get_recent_activity`, `get_active_work`, `workspace_summary`, `fork_instance`, `promote`, `promote_all`, `get_context`, `update_context`, `log_progress`.
- Fact: `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/conport/conport_mcp_stdio.py` exposes a similar unprefixed surface.
- Fact: `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/conport/enhanced_server.py` exposes prefixed JSON-RPC names such as `conport_get_context`, `conport_update_context`, `conport_log_decision`, `conport_get_decisions`, `conport_log_progress`, `conport_get_progress`, `conport_update_progress`, `conport_get_recent_activity`, `conport_get_active_work`, `conport_fork_instance`, `conport_promote`, `conport_promote_all`.

### Adapters/clients used by other systems

- Fact: `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/clients.py` contains `ConPortClient`.
- Fact: `/Users/hue/code/dopemux-mvp/services/serena/bridge_adapter.py` uses `DopeconBridge` rather than direct DB access as a compatibility adapter.

### Request/response schemas where discoverable

- Fact: ConPort decision/progress/custom-data shapes are proxied through Pydantic models in `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/routes.py`.
- Unknown: canonical ConPort-native schema authority was not directly located in checked-in source.

### Concrete execution path example: conport / dope-query interaction

1. Fact: dopemux-side MCP wiring creates a `conport` stdio entry that executes `conport-mcp`.
2. Fact: bridge-side consumers use `ConPortClient` in `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/clients.py`.
3. Fact: the active bridge proxies KG reads/writes at `/kg/custom_data`, `/kg/decisions`, and `/kg/progress` in `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/routes.py`.
4. Fact: `/Users/hue/code/dopemux-mvp/services/dope-query` contains only `auth/models.py` and tests in static inspection.
5. Inference: current runtime authority is on ConPort plus bridge surfaces; `dope-query` is not an established active runtime from repo inspection.

### Interface inconsistencies / duplicate entrypoints / dead paths

- Fact: tests disagree on ConPort MCP naming:
  - `/Users/hue/code/dopemux-mvp/tests/mcp/test_conport_mcp_real.py` expects prefixed names.
  - `/Users/hue/code/dopemux-mvp/tests/mcp/test_conport_surface_contract.py` exercises unprefixed functions.
- Fact: `/Users/hue/code/dopemux-mvp/services/dope-query` has no discovered runtime entrypoint, FastAPI app, or CLI in the inspected tree.
- Inference: `dope-query` is either incomplete, deprecated, or only partially vendored here.

## 5. dope-context

### Canonical entrypoints

- Fact: `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py` defines `mcp = FastMCP("dope-context")`.
- Fact: `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py` returns `canonical_entrypoint: "python -m src.mcp.server"` from `/info`.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/mcp/registry.yaml` registers both `dopemux-claude-context` and `dope-context` against the same docker service `dope-context`.

### CLI surface

- Fact: no standalone CLI was observed beyond MCP/server startup.

### FastAPI routes / major endpoints

- Fact: custom routes in `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py` include:
  - `/health`
  - `/info`
  - `/autoindex/bootstrap`
  - `/autoindex/status`

### MCP servers/tools

- Fact: observed tools in `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py` include:
  - `index_workspace`
  - `search_code`
  - `get_index_status`
  - `clear_index`
  - `index_docs`
  - `docs_search`
  - `configure_decision_auto_indexing`
  - `search_all`
  - `sync_workspace`
  - `sync_docs`
  - `get_search_metrics`
  - `clear_search_metrics`
  - `start_autonomous_indexing`
  - `stop_autonomous_indexing`
  - `get_autonomous_status`
  - `start_autonomous_docs_indexing`
  - `stop_autonomous_docs_indexing`
  - `get_chunk_complexity`

### Adapters/clients used by other systems

- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/mcp/registry.yaml` and resolver stack govern endpoint naming and resolution.
- Fact: dope-context optionally imports `dopecon_bridge_connector` in `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`.

### Request/response schemas where discoverable

- Fact: `/Users/hue/code/dopemux-mvp/services/dope-context/src/search/hybrid_search.py` implements deterministic ranking with explicit tie-breaking and RRF-style composition.
- Fact: `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py` returns structured JSON dictionaries from the MCP tools and custom routes.

### Concrete execution path example: dope-context retrieval workflow

1. Fact: the MCP tool entry is `search_code()` in `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`.
2. Fact: that server wires dense search, BM25, hybrid search, reranking, token budgeting, and metrics in the same file.
3. Fact: `search_all()` in the same file combines code search and docs search.
4. Fact: service discovery is available from `/info`, which advertises the runtime transport and canonical entrypoint.

### Interface inconsistencies / duplicate entrypoints / dead paths

- Fact: the header comment in `src/mcp/server.py` documents only four MCP tools, but the file exposes many more.
- Fact: `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/simple_server.py` is an alternate mock/simple MCP server.
- Fact: `/Users/hue/code/dopemux-mvp/mcp-proxy-config.yaml` references `bash services/dope-context/run_mcp.sh`.
- Fact: static inspection did not find `/Users/hue/code/dopemux-mvp/services/dope-context/run_mcp.sh`.
- Fact: tests in `/Users/hue/code/dopemux-mvp/tests/test_config_manager.py` and `/Users/hue/code/dopemux-mvp/tests/test_workspace_detection.py` still refer to that missing path.
- Inference: `services/dope-context/run_mcp.sh` is a dead or stale interface path.

## 6. dopecon-bridge

### Canonical entrypoints

- Fact: `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/main.py` is the active FastAPI app entrypoint and includes routers from `dopecon_bridge.routes`.
- Fact: `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/routes.py` explicitly states the bridge is adapter/proxy only and must not be canonical task/workflow/decision/progress authority.

### CLI surface

- Fact: no dedicated CLI was observed.

### FastAPI routes / major endpoints

- Fact: active routers in `dopecon_bridge/routes.py` are:
  - `/auth`
  - `/events`
  - `/tasks`
  - `/ddg`
  - `/route`
  - `/kg`
  - `/health`
  - `/`
- Fact: observed active behavior includes:
  - `/events` publish/history/stream style endpoints
  - `/tasks/parse-prd`, `/tasks/next/{project_id}`, `/tasks/{task_id}/status` fail closed with `409`
  - `/route/pm` blocks workflow-significant unsafe mutations
  - `/kg/custom_data`, `/kg/decisions`, `/kg/progress` proxy to active ConPort REST
  - `/ddg/decisions`, `/ddg/search`

### MCP servers/tools

- Fact: bridge clients in `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/clients.py` call MCP-like tool endpoints at `/api/tools/{tool_name}` on `task-orchestrator` and `leantime-bridge`.

### Adapters/clients used by other systems

- Fact: `MCPClientManager` and `ConPortClient` are defined in `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/clients.py`.
- Fact: `/Users/hue/code/dopemux-mvp/services/serena/bridge_adapter.py` depends on bridge client behavior.

### Request/response schemas where discoverable

- Fact: request/response models for bridge endpoints live in `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/routes.py`.

### Interface inconsistencies / duplicate entrypoints / dead paths

- Fact: `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/orchestrator_endpoints.py` defines `/orchestrator/*` routes and hardcodes `http://localhost:8001`, but static inspection did not show it being mounted by `main.py`.
- Fact: `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/kg_endpoints.py` defines another `/kg/*` router, but static inspection did not show it being mounted by `main.py`.
- Inference: `orchestrator_endpoints.py` and `kg_endpoints.py` are stale or dead alternate surfaces relative to `dopecon_bridge/routes.py`.

## 7. task-orchestrator

### Canonical entrypoints

- Fact: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` is the active FastAPI runtime.
- Fact: `app/main.py` initializes `FastMCP("Task-Orchestrator")`, loads MCP tools from `task_orchestrator.mcp`, and mounts workflow/PM routers.

### CLI surface

- Fact: dopemux workflow CLI calls into the task-orchestrator HTTP API through `_workflow_request()`.

### FastAPI routes / major endpoints

- Fact: `app/main.py` exposes `/health`, `/info`, `/metrics`, workflow CRUD, coordination APIs, and a coordination websocket.
- Fact: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/api/project_workflow.py` provides:
  - `GET /api/projects/{project_id}/workflow/queue`
  - `GET /api/projects/{project_id}/workflow/blockers`
  - `GET /api/projects/{project_id}/workflow/state`
  - `POST /api/projects/{project_id}/workflow/transition`
- Fact: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/api/pm_tools.py` provides:
  - `POST /api/pm/work-items/{task_id}/update`
  - `POST /api/pm/work-items/{task_id}/transition`
  - `POST /api/pm/work-items/{task_id}/progress`

### MCP servers/tools

- Fact: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/mcp/__init__.py` exposes tools including:
  - `start_session`
  - `end_session`
  - `decompose_task`
  - `log_decision`
  - `get_workflow_status`
  - `record_context_switch`
  - `assess_risk`
  - `analyze_dependencies`
  - `batch_tasks`
  - `get_adhd_state`
  - `get_task_recommendations`
  - `record_break`
  - `get_agent_status`

### Adapters/clients used by other systems

- Fact: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/core/coordinator.py` coordinates `WorkflowService`, `ConPortEventAdapter`, `CognitiveLoadBalancer`, and `MultiDirectionalSyncEngine`.
- Fact: `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/clients.py` targets task-orchestrator tool endpoints.

### Request/response schemas where discoverable

- Fact: workflow models are in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/models/workflow.py`.
- Fact: coordination models are in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/models/coordination.py`.

### Concrete execution path example: task orchestration workflow

1. Fact: dopemux user command `workflow ideas add` posts to `/api/workflow/ideas` via `_workflow_request()`.
2. Fact: task-orchestrator active runtime in `app/main.py` mounts workflow routers and MCP tools.
3. Fact: `PlaneCoordinator` in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/core/coordinator.py` is the orchestration integration point for workflow, ConPort events, and ADHD balancing.
4. Fact: PM-plane writes are normalized through `CanonicalReceipt` returns from `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/api/pm_tools.py`.

### Interface inconsistencies / duplicate entrypoints / dead paths

- Fact: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py` prints `UNSUPPORTED RUNTIME` and tells callers to use `app/main.py`.
- Fact: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/query_server.py` also prints `UNSUPPORTED RUNTIME`.
- Fact: those files still reference canonical port `3014`.
- Fact: `/Users/hue/code/dopemux-mvp/docker/compose.core.yml` configures task-orchestrator with `PORT=8000`.
- Fact: dopemux workflow helper defaults to `http://localhost:8000`.
- Fact: `/Users/hue/code/dopemux-mvp/mcp-proxy-config.yaml` references `services/task-orchestrator/server.py`.
- Fact: static inspection did not find `/Users/hue/code/dopemux-mvp/services/task-orchestrator/server.py`.
- Inference: port and launcher docs/config are drifted; `server.py` is a dead path.

## 8. adhd engine / services

### Canonical entrypoints

- Fact: `/Users/hue/code/dopemux-mvp/services/adhd_engine/main.py` is the FastAPI runtime and also defines FastMCP tools.

### CLI surface

- Fact: `/Users/hue/code/dopemux-mvp/services/adhd_engine/cli/adhd.py` defines an argparse CLI with commands such as `status`, `break`, `focus`, `check`, `voice`, `context save`, and `context restore`.

### FastAPI routes / major endpoints

- Fact: `main.py` exposes `/`, `/health`, `/metrics`, `/background-service/status`, and `/test`.
- Fact: `/Users/hue/code/dopemux-mvp/services/adhd_engine/api/routes.py` exposes a much larger API including:
  - `/assess-task`
  - `/energy-level/{user_id}`
  - `/attention-state/{user_id}`
  - `/recommend-break`
  - `/break-recommendation`
  - `/user-profile`
  - `/activity/{user_id}`
  - `/cognitive-load/{user_id}`
  - `/flow-state/{user_id}`
  - `/session-time/{user_id}`
  - `/breaks/{user_id}`
  - `/tasks/{user_id}`
  - `/tasks`
  - `/patterns/{user_id}`
  - `/code-complexity`
  - `/predict`
  - `/statusline/{user_id}`
  - `/metrics`
  - `/ws/stream`
  - `/override-prediction`
  - `/customization-settings/{user_id}` GET/POST
  - `/prediction-feedback/{user_id}`
  - `/trust-metrics/{user_id}`
  - `/trust-visualization/{user_id}`
  - `/automation-level/{user_id}`
  - `/state`
  - `/log-intent`
  - `/save-context`
  - `/unfinished-work`
  - `/record-progress`
  - `/external-activity`
  - `/log-git-event`

### MCP servers/tools

- Fact: `main.py` exposes FastMCP tools:
  - `get_cognitive_state`
  - `assess_task_complexity`

### Adapters/clients used by other systems

- Fact: task-orchestrator MCP surface includes ADHD-related tools such as `get_adhd_state` and `get_task_recommendations`.
- Fact: dope-context metadata reports `adhd_integration: True` in `/info`.

### Request/response schemas where discoverable

- Fact: Pydantic schemas live in `/Users/hue/code/dopemux-mvp/services/adhd_engine/api/schemas.py`.

### Interface inconsistencies / duplicate entrypoints / dead paths

- Fact: directory name is `adhd_engine`, while documentation indexes include `adhd-engine` as a key in `/Users/hue/code/dopemux-mvp/docs/docs_index.yaml`.
- Fact: the CLI defaults `ADHD_ENGINE_URL` to `http://localhost:3333`.
- Unknown: active container/service port authority was not fully reconciled from all configs in this pass.
- Fact: `api/routes.py` docstring claims six endpoints, but static inspection shows far more.

## 9. serena

### Canonical entrypoints

- Fact: `/Users/hue/code/dopemux-mvp/services/serena/mcp_server.py` is the checked-in MCP server implementation.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/mcp/registry.yaml` registers `serena` as an MCP server and points local execution to `serena start-mcp-server`.

### CLI surface

- Fact: the MCP registry supplies the local command string; no separate checked-in top-level CLI implementation was inspected in this pass.

### FastAPI routes / major endpoints

- Fact: `/Users/hue/code/dopemux-mvp/services/serena/http_server.py` exposes:
  - `/`
  - `/health`
  - `/api/metrics`
  - `/api/detections/summary`
  - `/api/patterns/top`
  - `/api/patterns/{pattern_id}`

### MCP servers/tools

- Fact: `/Users/hue/code/dopemux-mvp/services/serena/mcp_server.py` registers tools including:
  - `get_workspace_status`
  - `find_symbol`
  - `goto_definition`
  - `get_context`
  - `find_references`
  - `analyze_complexity`
  - `filter_by_focus`
  - `suggest_next_step`
  - `predict_navigation_from_git`
  - `find_similar_code`
  - `find_test_file`
  - `get_unified_complexity`
  - `get_reading_order`
  - `find_relationships`
  - `get_navigation_patterns`
  - `update_focus_mode`
  - `detect_untracked_work`
  - `track_untracked_work`
  - `snooze_untracked_work`
  - `ignore_untracked_work`
  - `suggest_branch_organization`
  - `get_pattern_stats`
  - `get_top_patterns`
  - `get_abandoned_work`
  - `mark_abandoned`
  - `get_abandonment_stats`
  - `get_metrics_dashboard`
  - `get_metric_history`
  - `save_metrics_snapshot`
  - `get_untracked_work_config`
  - `update_untracked_work_config`
  - `read_file`
  - `list_dir`

### Adapters/clients used by other systems

- Fact: `/Users/hue/code/dopemux-mvp/services/serena/bridge_adapter.py` routes Serena compatibility calls through DopeconBridge.

### Request/response schemas where discoverable

- Fact: tool schemas are implicit in `list_tools()` definitions inside `mcp_server.py`; HTTP dashboard schemas are returned from `http_server.py`.

### Concrete execution path example: serena interaction workflow

1. Fact: MCP client resolves the `serena` server through `/Users/hue/code/dopemux-mvp/src/dopemux/mcp/registry.yaml`.
2. Fact: active checked-in MCP runtime is `/Users/hue/code/dopemux-mvp/services/serena/mcp_server.py`.
3. Fact: Serena bridge-backed context/decision access goes through `/Users/hue/code/dopemux-mvp/services/serena/bridge_adapter.py`, which calls DopeconBridge client methods such as `recent_decisions`, `search_decisions`, `related_decisions`, and `related_text`.

### Interface inconsistencies / duplicate entrypoints / dead paths

- Fact: `bridge_adapter.py` identifies itself as `Serena v2 DopeconBridge Adapter`.
- Inference: there is naming drift between `v2` language and the active checked-in top-level service path `services/serena/...`.
- Unknown: whether docs that still refer to `services/serena/v2/...` are fully stale was not exhaustively verified in this pass.

## 10. repo-truth-extractor

### Canonical entrypoints

- Fact: `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/README.md` says the canonical extraction service is `repo-truth-extractor`.
- Fact: the same README says:
  - v5 is the active execution engine
  - v4 is the default contract layer
  - v3 is the fallback/legacy layer
- Fact: `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v5.py` is the active execution runner named by `dopemux extract truth-run`.
- Fact: `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v4.py` explicitly preserves v4 prompt/artifact contracts while executing v5.

### CLI surface

- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extract_commands.py` exposes `dopemux extract truth-run`.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` exposes `dopemux truth`.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` exposes `dopemux upgrades run`, `doctor`, `status`, `preflight`, `validate-live`, `trace`, and `promptset audit`.

### FastAPI routes / major endpoints

- Fact: no FastAPI service was identified for repo-truth-extractor; its primary surface is CLI/subprocess runners and generated artifacts.

### MCP servers/tools

- Fact: no MCP server was identified for repo-truth-extractor.

### Adapters/clients used by other systems

- Fact: `dopemux extract truth-run` uses hygiene module `services/repo-truth-extractor/extraction_hygiene.py` and then execs `run_extraction_v5.py`.
- Fact: legacy/wrapper runners and tests live under `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor`.

### Request/response schemas where discoverable

- Fact: v4 prompt/artifact contract files live under:
  - `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

### Concrete execution path example: repo-truth extraction / audit workflow

1. Fact: `dopemux extract truth-run` in `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extract_commands.py` performs:
   - optional v3-to-v5 run import
   - hygiene scan
   - optional cleanup
   - subprocess execution of `services/repo-truth-extractor/run_extraction_v5.py`
2. Fact: `run_extraction_v4.py` wraps v5 execution and rebuilds deterministic v4-normalized outputs under `extraction/repo-truth-extractor/v4/runs/RUN_ID/`.
3. Fact: README examples prefer `dopemux upgrades run --pipeline-version v5 ...`.

### Interface inconsistencies / duplicate entrypoints / dead paths

- Fact: README says canonical CLI examples use `dopemux upgrades run --pipeline-version v5`.
- Fact: repo also retains `dopemux truth`, `dopemux extractor`, and `dopemux extract truth-run`.
- Inference: there are multiple overlapping user-facing entrypaths into extraction, with `extractor` explicitly legacy and `truth` likely older wrapper-style.

## 11. relevant MCP / routing / agent surfaces

### Registry and resolver authority

- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/mcp/registry.yaml` states it is the source of truth for MCP server naming and transport metadata.
- Fact: `/Users/hue/code/dopemux-mvp/src/dopemux/mcp/resolver.py` resolves instance definitions in this order:
  - repo profile TOML
  - environment overrides
  - global fallback

### Concrete duplicate / competing MCP surfaces

- Fact: `dopemux-claude-context` and `dope-context` both point to the same docker service in `registry.yaml`.
- Fact: ConPort exposes both prefixed and unprefixed tool naming variants in different checked-in server files.
- Fact: Serena has both an MCP server (`mcp_server.py`) and separate HTTP dashboard (`http_server.py`).
- Fact: Dope-Memory has two checked-in MCP server implementations.

### Dead or hard-failing interface paths

- Fact: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py` exits with unsupported-runtime failure.
- Fact: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/query_server.py` exits with unsupported-runtime failure.
- Fact: `/Users/hue/code/dopemux-mvp/services/task-orchestrator/server.py` is referenced by MCP config but was not found in static inspection.
- Fact: `/Users/hue/code/dopemux-mvp/services/dope-context/run_mcp.sh` is referenced by config/tests but was not found in static inspection.
