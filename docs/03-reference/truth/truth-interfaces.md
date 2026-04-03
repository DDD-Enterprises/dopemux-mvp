---
id: TRUTH_INTERFACES
title: Truth Interfaces
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: Truth Interfaces (reference) for dopemux documentation and developer workflows.
---
# TRUTH_INTERFACES

Method:
- Concrete interfaces only.
- Entry paths are cited by exact file path.
- Where wiring conflicts, the contradiction is noted instead of normalized away.

## CLI Interfaces

### `dopemux`

- Authority:
  - `/Users/hue/code/dopemux-mvp/pyproject.toml`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py`
- Observed CLI surfaces relevant to this packet:
  - `dopemux kernel ...`
  - `dopemux extractor ...`
  - `dopemux upgrades ...`
  - `dopemux truth`
- Important notes:
  - `dopemux truth` is a legacy shortcut to `PipelineRunner`, not the same path used by `dopemux extractor` / `dopemux upgrades`.

### `dopetask` wrapper

- Authority:
  - `/Users/hue/code/dopemux-mvp/scripts/dopetask`
  - `/Users/hue/code/dopemux-mvp/.dopetask-pin`
- Observed behavior:
  - repo marker validation
  - local venv bootstrap
  - pinned install
  - exec to the external `dopetask` command

### Compatibility shim: `taskx`

- Authority:
  - `/Users/hue/code/dopemux-mvp/scripts/taskx`
- Observed behavior:
  - `exec` to `scripts/dopetask`
- Interface status:
  - Compatibility alias only in this pass.

## MCP Servers / Tools

### `dope-context`

- Authority:
  - `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`
- Observed MCP tools:
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
- Observed HTTP routes:
  - `/health`
  - `/info`
  - `/autoindex/bootstrap`
  - `/autoindex/status`
- Observed canonical runtime hint:
  - `python -m src.mcp.server`

### `conport`

- Authority:
  - `/Users/hue/code/dopemux-mvp/src/conport/memory_server.py`
- Observed MCP tools:
  - `mem.upsert`
  - `mem.search`
  - `graph.link`
  - `graph.neighbors`
- Observed HTTP endpoints in HTTP mode:
  - `GET /health`
  - `POST /api/mem/search`
  - `POST /api/mem/upsert`
  - `POST /api/graph/link`
  - `POST /api/graph/neighbors`
  - `/sse`
  - `/messages`

### `task-orchestrator`

- Authority:
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/mcp/__init__.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/mcp_stdio.py`
- Observed MCP tool families:
  - dependency and batching: `analyze_dependencies`, `batch_tasks`
  - ADHD/session: `get_adhd_state`, `get_task_recommendations`, `record_break`, `start_session`, `end_session`, `record_context_switch`
  - agent/workflow/risk: `get_agent_status`, `decompose_task`, `log_decision`, `get_workflow_status`, `assess_risk`
- Observed stdio entry:
  - `mcp_stdio.py` imports and runs the `mcp` object from `app.main`
- Contradiction:
  - Dockerfile still points at a conflicting module.

### `ADHD engine`

- Authority:
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine/main.py`
- Observed MCP tools:
  - `get_cognitive_state`
  - `assess_task_complexity`

### `working-memory-assistant` MCP logic

- Authority:
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/mcp/server.py`
- Observed state:
  - tool logic exists
  - runnable MCP transport/bootstrap not confirmed in this pass

## HTTP APIs

### `dope-memory`

- Authority:
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`
- Observed routes:
  - `GET /health`
  - `GET /`
  - `POST /tools/memory_search`
  - `POST /tools/memory_store`
  - `POST /tools/memory_recap`
  - `POST /tools/memory_mark_issue`
  - `POST /tools/memory_link_resolution`
  - `POST /tools/memory_replay_session`
  - `POST /tools/memory_correct`
  - `POST /tools/memory_generate_reflection`
  - `POST /tools/memory_reflections`
  - `POST /tools/memory_trajectory`

### `working-memory-assistant`

- Authority:
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/main.py`
- Observed routes:
  - `POST /snapshot`
  - `POST /recover`
  - `GET /contexts/{user_id}`
  - `GET /preferences/{user_id}`
  - `POST /preferences`
  - `POST /adhd-snapshot`
  - `POST /adhd-recover`
  - `GET /adhd-context/{user_id}`
  - `POST /should-snapshot/{user_id}`
  - `GET /health`
  - `GET /stats/{user_id}`

### `task-orchestrator`

- Authority:
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/api/project_workflow.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/api/pm_tools.py`
- Observed routes:
  - `GET /health`
  - `GET /info`
  - `GET /metrics`
  - `POST /api/workflow/ideas`
  - `GET /api/workflow/ideas`
  - `PATCH /api/workflow/ideas/{idea_id}`
  - `POST /api/workflow/ideas/{idea_id}/promote`
  - `POST /api/workflow/epics`
  - `GET /api/workflow/epics`
  - `PATCH /api/workflow/epics/{epic_id}`
  - `POST /api/coordination/operations`
  - `GET /api/coordination/health`
  - `GET /api/coordination/metrics`
  - `POST /api/coordination/events`
  - `GET /api/coordination/conflicts`
  - `POST /api/coordination/conflicts/{conflict_id}/resolve`
  - `GET /api/coordination/status`
  - `POST /api/coordination/test`
  - `GET /queue`
  - `GET /blockers`
  - `GET /state`
  - `POST /transition`
  - `POST /work-items/{task_id}/update`
  - `POST /work-items/{task_id}/transition`
  - `POST /work-items/{task_id}/progress`
  - `WS /ws/coordination`

### `dopecon-bridge`

- Authority:
  - `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/routes.py`
- Observed routes:
  - `POST /auth/token`
  - `POST /auth/refresh`
  - `GET /health`
  - `GET /`
  - `POST /events`
  - `GET /events/stream`
  - `GET /events/history`
  - `GET /events/{stream:path}`
  - `POST /events/tasks-imported`
  - `POST /events/session-started`
  - `POST /events/progress-updated`
  - `POST /tasks/parse-prd`
  - `GET /tasks/next/{project_id}`
  - `PATCH /tasks/{task_id}/status`
  - `POST /route/pm`
  - `POST /kg/custom_data`
  - `GET /kg/custom_data`
  - `POST /kg/decisions`
  - `GET /kg/decisions`
  - `POST /kg/progress`
  - `GET /kg/progress`
  - `GET /ddg/decisions`
  - `GET /ddg/search`

### `ADHD engine`

- Authority:
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine/main.py`
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine/api/routes.py`
- Observed root routes:
  - `/`
  - `/health`
  - `/metrics`
  - `/background-service/status`
  - `/test`
- Observed `/api/v1` route family members from `api/routes.py`:
  - `POST /assess-task`
  - `GET /energy-level/{user_id}`
  - `GET /attention-state/{user_id}`
  - `POST /recommend-break`
  - `POST /break-recommendation`
  - `POST /user-profile`
  - `PUT /activity/{user_id}`
  - `GET /cognitive-load/{user_id}`
  - `GET /flow-state/{user_id}`
  - `GET /session-time/{user_id}`
  - `GET /breaks/{user_id}`
  - `GET /tasks/{user_id}`
  - `GET /tasks`
  - `GET /patterns/{user_id}`
  - `POST /code-complexity`
  - `POST /predict`
  - `GET /statusline/{user_id}`
  - `GET /metrics`
  - `POST /override-prediction`
  - `POST /customization-settings/{user_id}`
  - `GET /customization-settings/{user_id}`
  - `POST /prediction-feedback/{user_id}`
  - `GET /trust-metrics/{user_id}`
  - `GET /trust-visualization/{user_id}`
  - `POST /automation-level/{user_id}`
  - `GET /state`
  - `POST /log-intent`
  - `POST /save-context`
  - `GET /unfinished-work`
  - `POST /record-progress`
  - `GET /external-activity`
  - `POST /log-git-event`

## Adapters / Clients

- `dopecon-bridge` client layer:
  - `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/clients.py`
  - Observed upstream tool routing:
    - `task-orchestrator` and `leantime-bridge` via HTTP `POST /api/tools/{tool_name}`
  - Observed ConPort direct routes:
    - `/api/decisions`
    - `/api/search/{workspace_id}`
    - `/api/progress`
    - `/api/custom_data`
- `task-orchestrator` workflow persistence adapter:
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py`
  - Uses `AsyncDopeconBridgeClient` to persist workflow custom data.
- `ADHD engine` ConPort client usage:
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine/core/activity_tracker.py`

## Important Execution Paths

### Dopemux-driven workflow

- Observed path:
  - `dopemux kernel <...>` -> `/Users/hue/code/dopemux-mvp/src/dopemux/commands/kernel_commands.py` -> `/Users/hue/code/dopemux-mvp/scripts/taskx` -> `/Users/hue/code/dopemux-mvp/scripts/dopetask` -> repo-local `.dopetask_venv/bin/dopetask`
- Drift note:
  - Operator-facing naming still says TaskX in places even though runtime lands in `dopetask`.

### Memory / context retrieval workflow

- Observed dope-memory retrieval path:
  - caller -> `POST /tools/memory_search` in `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`
  - chronicle lookup -> `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/chronicle/store.py`
  - trajectory boost -> dope-memory trajectory manager usage in the same runtime
  - deterministic sort -> boosted score, timestamp, id
  - storage -> `repo_root/.dopemux/chronicle.sqlite`
- Observed dope-context retrieval path:
  - caller -> `search_all` or search-specific MCP tool in `/Users/hue/code/dopemux-mvp/services/dope-context/src/mcp/server.py`
  - hybrid ranking -> deterministic tests under `/Users/hue/code/dopemux-mvp/services/dope-context/tests/test_hybrid_determinism.py`

### Orchestration / task workflow

- Observed path:
  - caller -> `/api/workflow/*` or `/work-items/*` in `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py` and router modules
  - workflow service -> `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_service.py`
  - persistence adapter -> `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/services/workflow_store.py`
  - bridge -> `AsyncDopeconBridgeClient`
  - downstream storage -> `dopecon-bridge` `/kg/custom_data`

### Repo-truth / audit workflow

- Observed canonical path:
  - `dopemux extractor ...` or `dopemux upgrades ...` -> `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extractor_commands.py`
  - runner resolution -> `run_extraction_v5.py`
  - subprocess execution in resolved repo root
  - artifacts -> `/Users/hue/code/dopemux-mvp/extraction/repo-truth-extractor/v3/runs`
- Observed legacy path:
  - `dopemux truth` -> `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` -> `PipelineRunner` in `/Users/hue/code/dopemux-mvp/src/dopemux/extractor/runner.py`
