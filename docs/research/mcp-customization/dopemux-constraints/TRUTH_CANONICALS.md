---
id: TRUTH_CANONICALS
title: Truth Canonicals
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: Truth Canonicals (reference) for dopemux documentation and developer workflows.
---
# TRUTH_CANONICALS

Method:
- `Observed` means directly read in code/config/tests.
- `Inference` means recommendation based on multiple observed signals.
- Confidence reflects canonical recommendation, not general system importance.

## Cluster: `src/dopemux` vs top-level `dopemux`

- Candidates:
  - `/Users/hue/code/dopemux-mvp/src/dopemux`
  - `/Users/hue/code/dopemux-mvp/dopemux`
- Evidence for `/Users/hue/code/dopemux-mvp/src/dopemux`:
  - `pyproject.toml` package discovery uses `where = ["src"]`.
  - `pyproject.toml` exports `dopemux = "dopemux.cli:main"`.
  - `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` contains the active CLI.
- Evidence for `/Users/hue/code/dopemux-mvp/dopemux`:
  - Observed only `__init__.py`.
  - No competing CLI/runtime evidence found.
- Canonical recommendation:
  - `/Users/hue/code/dopemux-mvp/src/dopemux`
- Confidence:
  - HIGH
- Unresolved questions:
  - None material for this packet.

## Cluster: `dopetask` vs `taskx` vs TaskX naming

- Candidates:
  - `/Users/hue/code/dopemux-mvp/scripts/dopetask`
  - `/Users/hue/code/dopemux-mvp/scripts/taskx`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/commands/kernel_commands.py`
  - `/Users/hue/code/dopemux-mvp/README.md`
- Evidence for `scripts/dopetask`:
  - Enforces `.dopetaskroot` and `.dopetask-pin`.
  - Creates `.dopetask_venv`.
  - Installs pinned package from `.dopetask-pin`.
  - Execs the `dopetask` binary.
- Evidence for `scripts/taskx`:
  - Compatibility shim that execs `scripts/dopetask`.
- Evidence for TaskX naming:
  - `kernel_commands.py` still prints/help-texts in TaskX terms and delegates to `scripts/taskx`.
  - `tests/unit/test_cli_kernel_commands.py` still expects TaskX naming.
- Evidence for README:
  - Mentions an older `dopetask==0.2.0` pin while `.dopetask-pin` and `pyproject.toml` point at `0.5.1`.
- Canonical recommendation:
  - Runtime authority: `/Users/hue/code/dopemux-mvp/scripts/dopetask`
  - Compatibility alias only: `/Users/hue/code/dopemux-mvp/scripts/taskx`
  - Naming/documentation authority is unresolved because repo messaging still mixes `TaskX` and `dopetask`.
- Confidence:
  - HIGH for runtime authority
  - LOW for naming authority
- Unresolved questions:
  - Whether `dopemux kernel` should continue exposing TaskX language for operator continuity or be renamed to dopetask-first semantics.

## Cluster: `dope-memory` runtime vs adapters vs WMA MCP logic

- Candidates:
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`
  - `/Users/hue/code/dopemux-mvp/services/dope-memory/mcp_stdio_adapter.py`
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/mcp/server.py`
- Evidence for `dope_memory_main.py`:
  - Docstring identifies canonical entry point for the Dope-Memory service.
  - `compose.yml` `dope-memory` service builds from the working-memory-assistant Dockerfile and runs this entrypoint.
  - Exposes `/tools/*` HTTP endpoints and `/health`.
- Evidence for `mcp_stdio_adapter.py`:
  - Thin HTTP proxy only.
  - Hard-codes `http://localhost:8096/tools/...`, which conflicts with registry/compose port `3020`.
- Evidence for `mcp/server.py`:
  - Implements tool logic class surface.
  - No directly observed runnable MCP transport/bootstrap.
- Canonical recommendation:
  - `/Users/hue/code/dopemux-mvp/services/working-memory-assistant/dope_memory_main.py`
- Confidence:
  - HIGH
- Unresolved questions:
  - Whether a supported stdio MCP wrapper exists elsewhere for the same tool set.

## Cluster: `conport` vs `dope-query`

- Candidates:
  - `/Users/hue/code/dopemux-mvp/src/conport/memory_server.py`
  - `/Users/hue/code/dopemux-mvp/services/dope-query`
- Evidence for `src/conport/memory_server.py`:
  - Active MCP server with tool registration.
  - Active HTTP mode with `/health` and `/api/*` endpoints.
  - Hybrid Milvus plus PostgreSQL behavior is directly coded.
- Evidence for `services/dope-query`:
  - Sparse files.
  - No active runtime entrypoint observed.
  - No compose or registry authority located during this pass.
- Canonical recommendation:
  - `/Users/hue/code/dopemux-mvp/src/conport/memory_server.py`
- Confidence:
  - HIGH
- Unresolved questions:
  - Whether `services/dope-query` is an abandoned precursor, a reserved namespace, or intentionally dormant.

## Cluster: task-orchestrator active runtime vs hard-failing legacy module

- Candidates:
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/mcp_stdio.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/Dockerfile`
- Evidence for `app/main.py`:
  - Creates FastAPI runtime and `FastMCP("Task-Orchestrator")`.
  - Includes workflow and PM routers.
  - `mcp_stdio.py` imports MCP object from `app.main`.
- Evidence for `task_orchestrator/app.py`:
  - Raises hard failure and says it is no longer a supported runtime.
  - Claims canonical runtime is `app/main.py (Port 3014)`.
- Evidence for Dockerfile:
  - `CMD ["uvicorn", "task_orchestrator.app:app", ...]` points at the hard-failing module.
- Evidence for deployment metadata:
  - `services/registry.yaml` and `compose.yml` use port `8000`, not `3014`.
- Canonical recommendation:
  - Runtime authority should be `/Users/hue/code/dopemux-mvp/services/task-orchestrator/app/main.py`
  - Actual Docker runtime canonicality is unresolved because the checked-in Dockerfile points elsewhere.
- Confidence:
  - MEDIUM
- Unresolved questions:
  - Whether the Dockerfile is stale, or whether packaging/import resolution makes `task_orchestrator.app:app` resolve differently in image builds.

## Cluster: dopecon-bridge package runtime vs older top-level endpoint files

- Candidates:
  - `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/main.py`
  - `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge/routes.py`
  - older top-level modules under `/Users/hue/code/dopemux-mvp/services/dopecon-bridge`
- Evidence for package runtime:
  - `main.py` assembles routers from `dopecon_bridge.routes`.
  - `dopecon_bridge/app.py` delegates to `main.py`.
  - `routes.py` contains the active contract language and route definitions.
- Evidence for top-level legacy modules:
  - Files exist, but active entrypoint now imports the packaged router set instead.
- Canonical recommendation:
  - `/Users/hue/code/dopemux-mvp/services/dopecon-bridge/dopecon_bridge`
- Confidence:
  - HIGH
- Unresolved questions:
  - Which older top-level modules are still imported indirectly by tests or scripts outside the active HTTP runtime.

## Cluster: `adhd_engine` vs `adhd-engine`

- Candidates:
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine`
  - `/Users/hue/code/dopemux-mvp/services/adhd-engine`
- Evidence for `services/adhd_engine`:
  - Contains FastAPI app, MCP tools, Dockerfile, and broad API route surface.
  - `compose.yml` builds `adhd-engine` from `/Users/hue/code/dopemux-mvp/services/adhd_engine/Dockerfile`.
- Evidence for `services/adhd-engine`:
  - Observed as a tiny duplicate residue with limited files.
- Canonical recommendation:
  - `/Users/hue/code/dopemux-mvp/services/adhd_engine`
- Confidence:
  - HIGH
- Unresolved questions:
  - Whether any external scripts still import from the hyphenated duplicate path via shell assumptions.

## Cluster: Serena in-repo implementation vs Docker wrapper/external Serena

- Candidates:
  - `/Users/hue/code/dopemux-mvp/services/serena`
  - `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/serena`
  - `/Users/hue/code/dopemux-mvp/mcp-proxy-config.json`
  - `/Users/hue/code/dopemux-mvp/mcp-proxy-config.yaml`
  - `/Users/hue/code/dopemux-mvp/mcp-proxy-config.copilot.yaml`
- Evidence for Docker wrapper:
  - `compose.yml` builds Serena from `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/serena`.
  - Wrapper Dockerfile installs external Serena from Git at a pinned revision and runs proxy/startup scripts.
- Evidence for in-repo `services/serena`:
  - Large codebase with `mcp_server.py`, `http_server.py`, and tests.
  - Not the compose build target during this pass.
- Evidence from config:
  - `mcp-proxy-config.json` and `.copilot.yaml` use localhost SSE on `3006`.
  - `mcp-proxy-config.yaml` uses a different `docker exec` route and `python server.py`.
  - `claude_config.py` maps `serena-v2`, `serena`, and `dopemux-serena` aliases.
- Canonical recommendation:
  - Deployment/runtime authority leans toward `/Users/hue/code/dopemux-mvp/docker/mcp-servers-source/serena`
  - In-repo implementation remains `UNKNOWN` as canonical development authority.
- Confidence:
  - LOW
- Unresolved questions:
  - Whether `/Users/hue/code/dopemux-mvp/services/serena` is a fork intended to replace the wrapper.
  - Which Serena surface downstream tools should target when they ask for `serena-v2`.

## Cluster: repo-truth-extractor v5/v4 vs legacy `dopemux truth`

- Candidates:
  - `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v5.py`
  - `/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v4.py`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/commands/extractor_commands.py`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/extractor/runner.py`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/cli.py` `truth` command
- Evidence for v5/v4 extractor family:
  - README names the service the canonical extraction system.
  - `extractor_commands.py` resolves and runs `run_extraction_v5.py`.
  - `run_extraction_v4.py` explicitly wraps v5 for v4 contract compatibility.
- Evidence for legacy runner:
  - `src/dopemux/cli.py` `truth` command instantiates `PipelineRunner`.
  - `PipelineRunner` emits legacy trace behavior and dry-run/execution ritual language.
- Canonical recommendation:
  - Repo-truth extraction authority: `run_extraction_v5.py` via `dopemux upgrades` / extractor commands
  - Legacy alias/drift: `dopemux truth` via `PipelineRunner`
- Confidence:
  - HIGH
- Unresolved questions:
  - Whether `dopemux truth` is intentionally kept as a legacy shortcut or is simply stale CLI drift.

## Cluster: agent families

- Candidates:
  - `/Users/hue/code/dopemux-mvp/services/agents`
  - `/Users/hue/code/dopemux-mvp/src/dopemux/agent_orchestrator.py`
  - `/Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/agents`
- Evidence for `services/agents`:
  - README says only MemoryAgent is implemented and others are pending.
- Evidence for `src/dopemux/agent_orchestrator.py`:
  - Contains a fuller task queue/orchestration model with LiteLLM integration.
- Evidence for task-orchestrator agent package:
  - Contains its own agent pool and assignment heuristics.
- Canonical recommendation:
  - `UNKNOWN`
- Confidence:
  - LOW
- Unresolved questions:
  - Which agent family is intended to be operator-facing.
  - Whether one family is a library layer and another is the runtime surface.
