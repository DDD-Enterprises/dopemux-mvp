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

Authority order note:
- Active Task Packets control scoped execution and allowlists for the current work slice.
- Runtime code, config, compose wiring, tests, and active entrypoints govern behavior claims.
- This truth artifact records evidence-backed canonical recommendations, but it does not outrank runtime/source truth.
- Generated, advisory, extracted, exploratory, or external artifacts remain evidence only unless runtime/source truth supports them.
- Preserve `UNKNOWN` where this artifact does not settle authority.

## Cluster: `src/dopemux` vs top-level `dopemux`

- Candidates:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
- Evidence for `[LOCAL_PATH_REDACTED]`:
  - `pyproject.toml` package discovery uses `where = ["src"]`.
  - `pyproject.toml` exports `dopemux = "dopemux.cli:main"`.
  - `[LOCAL_PATH_REDACTED]` contains the active CLI.
- Evidence for `[LOCAL_PATH_REDACTED]`:
  - Observed only `__init__.py`.
  - No competing CLI/runtime evidence found.
- Canonical recommendation:
  - `[LOCAL_PATH_REDACTED]`
- Confidence:
  - HIGH
- Unresolved questions:
  - None material for this packet.

## Cluster: `dopetask` vs `taskx` vs TaskX naming

- Candidates:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
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
  - Runtime authority: `[LOCAL_PATH_REDACTED]`
  - Compatibility alias only: `[LOCAL_PATH_REDACTED]`
  - Naming/documentation authority is unresolved because repo messaging still mixes `TaskX` and `dopetask`.
- Confidence:
  - HIGH for runtime authority
  - LOW for naming authority
- Unresolved questions:
  - Whether `dopemux kernel` should continue exposing TaskX language for operator continuity or be renamed to dopetask-first semantics.

## Cluster: `dope-memory` runtime vs adapters vs WMA MCP logic

- Candidates:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
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
  - `[LOCAL_PATH_REDACTED]`
- Confidence:
  - HIGH
- Unresolved questions:
  - Whether a supported stdio MCP wrapper exists elsewhere for the same tool set.

## Cluster: `conport` vs `dope-query`

- Candidates:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
- Evidence for `src/conport/memory_server.py`:
  - Active MCP server with tool registration.
  - Active HTTP mode with `/health` and `/api/*` endpoints.
  - Hybrid Milvus plus PostgreSQL behavior is directly coded.
- Evidence for `services/dope-query`:
  - Sparse files.
  - No active runtime entrypoint observed.
  - No compose or registry authority located during this pass.
- Canonical recommendation:
  - `[LOCAL_PATH_REDACTED]`
- Confidence:
  - HIGH
- Unresolved questions:
  - Whether `services/dope-query` is an abandoned precursor, a reserved namespace, or intentionally dormant.

## Cluster: task-orchestrator active runtime vs hard-failing legacy module

- Candidates:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
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
  - Runtime authority should be `[LOCAL_PATH_REDACTED]`
  - Actual Docker runtime canonicality is unresolved because the checked-in Dockerfile points elsewhere.
- Confidence:
  - MEDIUM
- Unresolved questions:
  - Whether the Dockerfile is stale, or whether packaging/import resolution makes `task_orchestrator.app:app` resolve differently in image builds.

## Cluster: dopecon-bridge package runtime vs older top-level endpoint files

- Candidates:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - older top-level modules under `[LOCAL_PATH_REDACTED]`
- Evidence for package runtime:
  - `main.py` assembles routers from `dopecon_bridge.routes`.
  - `dopecon_bridge/app.py` delegates to `main.py`.
  - `routes.py` contains the active contract language and route definitions.
- Evidence for top-level legacy modules:
  - Files exist, but active entrypoint now imports the packaged router set instead.
- Canonical recommendation:
  - `[LOCAL_PATH_REDACTED]`
- Confidence:
  - HIGH
- Unresolved questions:
  - Which older top-level modules are still imported indirectly by tests or scripts outside the active HTTP runtime.

## Cluster: `adhd_engine` vs `adhd-engine`

- Candidates:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
- Evidence for `services/adhd_engine`:
  - Contains FastAPI app, MCP tools, Dockerfile, and broad API route surface.
  - `compose.yml` builds `adhd-engine` from `[LOCAL_PATH_REDACTED]`.
- Evidence for `services/adhd-engine`:
  - Observed as a tiny duplicate residue with limited files.
- Canonical recommendation:
  - `[LOCAL_PATH_REDACTED]`
- Confidence:
  - HIGH
- Unresolved questions:
  - Whether any external scripts still import from the hyphenated duplicate path via shell assumptions.

## Cluster: Serena in-repo implementation vs Docker wrapper/external Serena

- Candidates:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
- Evidence for Docker wrapper:
  - `compose.yml` builds Serena from `[LOCAL_PATH_REDACTED]`.
  - Wrapper Dockerfile installs external Serena from Git at a pinned revision and runs proxy/startup scripts.
- Evidence for in-repo `services/serena`:
  - Large codebase with `mcp_server.py`, `http_server.py`, and tests.
  - Not the compose build target during this pass.
- Evidence from config:
  - `mcp-proxy-config.json` and `.copilot.yaml` use localhost SSE on `3006`.
  - `mcp-proxy-config.yaml` uses a different `docker exec` route and `python server.py`.
  - `claude_config.py` maps `serena-v2`, `serena`, and `dopemux-serena` aliases.
- Canonical recommendation:
  - Deployment/runtime authority leans toward `[LOCAL_PATH_REDACTED]`
  - In-repo implementation remains `UNKNOWN` as canonical development authority.
- Confidence:
  - LOW
- Unresolved questions:
  - Whether `[LOCAL_PATH_REDACTED]` is a fork intended to replace the wrapper.
  - Which Serena surface downstream tools should target when they ask for `serena-v2`.

## Cluster: repo-truth-extractor v5/v4 vs legacy `dopemux truth`

- Candidates:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]` `rte` command group
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]` `truth` command
- Evidence for v5/v4 extractor family:
  - `src/dopemux/cli.py` registers `dopemux rte` as the "Canonical operator entrypoint for Repo Truth Extractor."
  - `src/dopemux/cli.py` attaches `run`, `list`, `doctor`, `status`, `preflight`, `validate-live`, `trace`, and `promptset` commands to `dopemux rte`.
  - `src/dopemux/cli.py` labels `dopemux upgrades` as a legacy compatibility alias for `dopemux rte`.
  - `extractor_commands.py` resolves and runs `run_extraction_v5.py` through the shared command implementation.
  - `run_extraction_v4.py` explicitly wraps v5 for v4 contract compatibility.
- Evidence for legacy runner:
  - `src/dopemux/cli.py` `truth` command raises a refusal pointing to `dopemux rte`.
  - Older `PipelineRunner` surfaces remain legacy drift and are not the v5 path.
- Canonical recommendation:
  - Repo-truth operator command family: `dopemux rte`
  - Strongest v5 extraction runtime authority: `run_extraction_v5.py`
  - Legacy compatibility alias: `dopemux upgrades`
  - Deprecated/refusal paths: `dopemux extractor`, `dopemux truth`, hidden `dopemux extract truth-run`
  - Advanced/debug/manual direct runner path: `python services/repo-truth-extractor/run_extraction_v5.py ...`
- Confidence:
  - HIGH
- Unresolved questions:
  - Whether every older operator-facing document has been updated away from stale command framing.

## Cluster: agent families

- Candidates:
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
  - `[LOCAL_PATH_REDACTED]`
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
