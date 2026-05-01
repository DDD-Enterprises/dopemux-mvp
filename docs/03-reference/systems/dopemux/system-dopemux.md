---
id: SYSTEM_Dopemux
title: System Dopemux
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: System Dopemux (reference) for dopemux documentation and developer workflows.
---
### 1. Purpose

`dopemux` is the repo’s operator-facing control layer and CLI package. Observed in `pyproject.toml` and `src/dopemux/cli.py`, it exposes the main `dopemux` command, launches local operator workflows, manages routing mode and MCP startup, delegates kernel lifecycle commands to the external `dopetask` runner, and routes operator actions and startup/configuration flows toward downstream systems such as task-orchestrator, dope-memory, ConPort, and dope-context. It does not own canonical PM state, canonical durable memory, structured retrieval truth, or a proven single agent runtime authority.

### 2. Core Responsibilities

- CLI entrypoint and command registration.
  Observed: `pyproject.toml` exports `dopemux = "dopemux.cli:main"`, and `src/dopemux/cli.py` registers top-level groups including `kernel`, `mcp`, `routing`, `instances`, `health`, `workflow`, `memory`, `extractor`, and `tmux`.

- Operator startup and local environment coordination.
  Observed: `src/dopemux/cli.py` `start(...)` loads routing config, validates workspace state, can export instance-scoped environment files under `.dopemux/env`, can auto-configure workspace MCP settings, and launches Claude Code through `ClaudeLauncher`.

- Task execution routing to the external dopetask runtime.
  Observed: `src/dopemux/commands/kernel_commands.py` delegates `doctor`, `compile`, `run`, `collect`, `gate`, `promote`, `feedback`, and `loop` to `scripts/taskx`; `scripts/taskx` is only a shim that execs `scripts/dopetask`; `scripts/dopetask` installs the pinned `dopetask` version from `.dopetask-pin` into `.dopetask_venv` and execs the external `dopetask` binary.

- MCP stack provisioning, startup, and health visibility.
  Observed: `src/dopemux/commands/mcp_commands.py` starts and stops Docker-based MCP services; `src/dopemux/cli.py` `_start_mcp_servers_with_progress(...)` provisions the stack, materializes instance overlays, launches Docker Compose, and runs a discovery gate.

- Routing mode management for LiteLLM and Claude Code Router.
  Observed: `src/dopemux/routing_cli.py` exposes `install`, `start`, `stop`, `reload`, `api`, `direct`, `uninstall`, `status`, and `health`; `src/dopemux/launchd_services.py` generates `~/.dopemux/routing.env` and wrapper scripts for LiteLLM and CCR; `src/dopemux/cli.py` `start(...)` applies routing mode and can repair unhealthy routing services.

- Workspace-specific MCP configuration updates.
  Observed: `src/dopemux/auto_configurator.py` rewrites ConPort MCP arguments to include `--workspace_id` and rewrites dope-context command paths for the current workspace.

- Health and status reporting across the local stack.
  Observed: `src/dopemux/health.py` checks Dopemux core state, DopeBrainz processes, MCP servers, Docker services, system resources, and ADHD feature surfaces; `src/dopemux/cli.py` exposes a `health` command using that checker.

- PM-plane routing and adapter wiring, not PM authority.
  Observed: `src/dopemux/pm/writes.py` classifies PM writes, routes metadata updates to Leantime, routes workflow transitions to task-orchestrator, and records mirror receipts. Inference: `dopemux` acts as a PM-plane coordinator, not a PM system of record, because the write functions explicitly route authority outward.

- dope-context startup triggering.
  Observed: `src/dopemux/cli.py` `_trigger_dope_context_autoindex_startup(...)` POSTs to `DOPE_CONTEXT_URL` or `http://localhost:3010` at `/autoindex/bootstrap` with the current workspace path and non-blocking startup parameters.

### 3. Non-Responsibilities

- Canonical durable memory storage.
  Observed: `src/dopemux/memory/capture_client.py` resolves and writes against working-memory-assistant chronicle schema and migrations; `src/dopemux/pm/adapters/dope_memory.py` calls external dope-memory `/tools/*` endpoints. `dopemux` is a client/coordinator here, not the durable memory runtime.

- Canonical PM truth authority.
  Observed: `src/dopemux/pm/writes.py` states Leantime is the authority for metadata writes and task-orchestrator is the authority for workflow transitions. `dopemux` routes writes but does not declare itself canonical.

- Structured memory authority for ConPort.
  Observed: `src/dopemux/pm/adapters/conport.py` and `src/dopemux/tools/conport_client.py` are HTTP clients for ConPort endpoints. They do not implement ConPort storage or graph authority.

- Retrieval authority for dope-context.
  Observed: `src/dopemux/auto_configurator.py` and `src/dopemux/cli.py` only configure and trigger dope-context. They do not implement the retrieval service itself.

- dopetask runtime ownership.
  Observed: `scripts/dopetask` installs and execs an external `dopetask` package. `dopemux` delegates into it.

- Proven single agent runtime ownership.
  Observed: the repo contains multiple agent families (`src/dopemux/agent_orchestrator.py`, `services/agents`, and task-orchestrator agent code per the truth pack). No single canonical agent runtime authority is proven from the `dopemux` package alone. Authority is `UNKNOWN`.

- Canonical repo-truth extraction runtime.
  Observed: the repo-truth pack identifies `services/repo-truth-extractor/run_extraction_v5.py` as the canonical extraction path. `dopemux` only wires commands into that surface.

### 4. Key Surfaces

- Commands: CLI console script `dopemux`.
  Observed: declared in `pyproject.toml` and implemented in `src/dopemux/cli.py`.

- Commands: main operator startup `dopemux start`.
  Observed: `src/dopemux/cli.py` `start(...)` handles routing mode, workspace validation, MCP startup, dope-context startup bootstrap, role activation, and Claude launch.

- Commands: `dopemux routing ...`.
  Observed: `src/dopemux/routing_cli.py` defines `install`, `start`, `stop`, `reload`, `api`, `direct`, `uninstall`, `status`, and `health`.

- Commands: `dopemux mcp ...` and alias `dopemux servers ...`.
  Observed: `src/dopemux/commands/mcp_commands.py` defines `up`, `down`, `status`, `logs`, and `start-all`.

- Commands: `dopemux kernel ...`.
  Observed: `src/dopemux/commands/kernel_commands.py` defines `doctor`, `compile`, `run`, `collect`, `gate`, `promote`, `feedback`, and `loop`, all delegated through the taskx-to-dopetask wrapper chain.

- Commands: health and instance commands.
  Observed: `src/dopemux/cli.py` registers `health`; `src/dopemux/commands/instances_commands.py` manages instance listing, resume, and cleanup.

- Scripts.
  Observed: `scripts/dopetask` is the real pinned runner bootstrap; `scripts/taskx` is a compatibility shim only.

- Config surfaces.
  Observed: `src/dopemux/routing_config.py` is used by routing and startup flow; `src/dopemux/mcp/registry.py` loads canonical MCP definitions from `src/dopemux/mcp/registry.yaml`; `src/dopemux/auto_configurator.py` rewrites `~/.claude.json` project MCP entries; `src/dopemux/cli.py` writes `.dopemux/env/instance_*.sh` and `.dopemux/env/instance_*.env`.

- Environment surfaces.
  Observed: `DOPEMUX_INSTANCE_ID`, `DOPEMUX_WORKSPACE_ID`, `DOPEMUX_EXPORT_SECRETS`, `DOPEMUX_ROUTING_MODE`, `DOPEMUX_CCR_API_KEY`, `DOPEMUX_LITELLM_MASTER_KEY`, `DOPEMUX_LITELLM_DB_URL`, `TASK_ORCHESTRATOR_URL`, `DOPE_MEMORY_URL`, `CONPORT_URL`, `DOPE_CONTEXT_URL`, `DOPEMUX_AUTO_INDEX_ON_STARTUP`, `DOPEMUX_AUTO_INDEX_DEBOUNCE_SECONDS`, `DOPEMUX_AUTO_INDEX_PERIODIC_SECONDS`, `DOPEMUX_SKIP_MCP_START`, `DOPEMUX_LEGACY_DETECTION`.

### 5. System Boundaries

- `dopetask`
  - What dopemux calls: kernel commands invoke `scripts/taskx`, which execs `scripts/dopetask`; `scripts/dopetask` installs and execs the external `dopetask` CLI.
  - What dopemux receives: process exit status only is directly observed in `kernel_commands.py`.
  - What dopemux does not control: dopetask implementation, lifecycle semantics, and internal storage are outside the `dopemux` package.

- `task-orchestrator`
  - What dopemux calls: `src/dopemux/pm/adapters/orchestrator.py` calls HTTP endpoints such as `/api/projects/{project_id}/workflow/transition`, `/workflow/queue`, `/workflow/state`, `/workflow/blockers`, and `/context`.
  - What dopemux receives: JSON workflow state, queue, blocker, context, and transition responses.
  - What dopemux does not control: canonical workflow authority and PM transition rules. `src/dopemux/pm/writes.py` treats task-orchestrator as workflow authority.

- `dope-memory`
  - What dopemux calls: `src/dopemux/pm/adapters/dope_memory.py` calls external HTTP endpoints `/tools/memory_search`, `/tools/memory_store`, and `/tools/memory_correct`.
  - What dopemux writes locally: `src/dopemux/memory/capture_client.py` uses working-memory-assistant chronicle schema and migrations for local capture ledger handling under repo-local markers.
  - What dopemux receives: JSON search/store/correct responses from the external service and local ledger write results from capture handling.
  - What dopemux does not control: canonical durable memory service behavior or PM status authority.

- `ConPort`
  - What dopemux calls: `src/dopemux/pm/adapters/conport.py` calls `/kg/custom_data`, `/api/decisions`, and `/kg/health`; `src/dopemux/tools/conport_client.py` calls `/health`, `/api/context/{workspace_id}`, `/api/decisions`, `/api/progress`, and semantic search endpoints.
  - What dopemux receives: health responses, decision/progress/context payloads, and custom-data results.
  - What dopemux does not control: ConPort graph storage, vector retrieval, or structured memory authority.

- `dope-context`
  - What dopemux calls: `src/dopemux/cli.py` POSTs to `/autoindex/bootstrap`; `src/dopemux/auto_configurator.py` rewrites dope-context command paths in Claude project config.
  - What dopemux receives: bootstrap status payloads such as `started`, `already_running`, or error status.
  - What dopemux does not control: indexing algorithms, retrieval ranking, contracts, or storage backends of dope-context.

- `MCP / routing layer`
  - What dopemux calls: Docker Compose through `mcp` commands and `_start_mcp_servers_with_progress(...)`; launchd-managed LiteLLM and CCR through `routing` commands and `LaunchdServiceManager`.
  - What dopemux receives: Docker process status, discovery-gate pass/fail, service status, and health responses.
  - What dopemux does not control: the internal runtime logic of individual MCP services. It provisions, starts, checks, and configures them.

### 6. Authority Model

- `dopemux` is an orchestration and operator-control layer.
  Observed: the active console script points to `dopemux.cli:main`, and the package primarily registers commands, launches subprocesses, writes env/config overlays, and calls external HTTP services.

- `dopemux` is authoritative for operator workflow initiation and local coordination behavior, but not for downstream domain truth.
  Inference: the code proves authority over local command dispatch, startup behavior, environment shaping, and integration routing, while routing PM, memory, and retrieval operations outward to other systems.

- `dopemux` does not own canonical data planes.
  Observed: PM writes in `src/dopemux/pm/writes.py` route to Leantime and task-orchestrator; ConPort and dope-memory access is through adapters/clients; dope-context is configured and triggered, not implemented here.

- `dopemux` depends on other systems for memory.
  Observed: dope-memory and working-memory-assistant chronicle surfaces are external dependencies of `src/dopemux/memory/capture_client.py` and `src/dopemux/pm/adapters/dope_memory.py`.

- `dopemux` depends on other systems for PM state.
  Observed: PM metadata and transitions are delegated to Leantime and task-orchestrator in `src/dopemux/pm/writes.py`.

- `dopemux` depends on other systems for retrieval.
  Observed: ConPort and dope-context are accessed through configuration, HTTP clients, and startup hooks.

- `dopemux` depends on other systems for agent execution.
  Observed: agent runtime authority is not established inside `src/dopemux/*` alone. Canonicality is `UNKNOWN`.

### 7. Known Drift / Issues

- CLI import path is currently broken in this checkout.
  Observed: `python -m dopemux.cli --help` fails with `ModuleNotFoundError: No module named 'core'` while importing `dopemux.pm.reads`.

- Kernel naming still drifts between TaskX and dopetask.
  Observed: `src/dopemux/commands/kernel_commands.py` talks about TaskX and invokes `scripts/taskx`; `scripts/taskx` is only a shim to `scripts/dopetask`; the truth pack also flags this naming drift.

- Operator routing and startup surfaces are duplicated or overlapping.
  Observed: `src/dopemux/cli.py` contains substantial routing behavior in `start(...)` while also registering a separate `routing` command group from `src/dopemux/routing_cli.py`.

- dope-context launch assumptions may drift from runtime reality.
  Observed: `src/dopemux/auto_configurator.py` still contains logic to rewrite a `services/dope-context/run_mcp.sh` style command path, while the truth pack flags missing `services/dope-context/run_mcp.sh` references in MCP proxy configs.

- PM authority is intentionally split, not unified.
  Observed: `src/dopemux/pm/writes.py` sends metadata to Leantime and transitions to task-orchestrator. Operators should not treat `dopemux` as a single PM source of truth.

- Multiple agent families exist with unresolved canonical runtime authority.
  Observed: the truth pack identifies agent duplication across `src/dopemux/agent_orchestrator.py`, `services/agents`, and task-orchestrator agents. `dopemux` should not be documented as owning agent runtime authority.

- Some service naming and port assumptions are hard-coded in clients.
  Observed: adapters default to `CONPORT_URL=http://localhost:3004`, `TASK_ORCHESTRATOR_URL=http://localhost:3014`, `DOPE_MEMORY_URL=http://localhost:3020`, and `DOPE_CONTEXT_URL=http://localhost:3010`. These defaults may diverge from compose or registry surfaces elsewhere.

### 8. Working Rules

- Verify `src/dopemux/*`, scripts, and executable behavior before trusting older docs.

- Trace operator actions through the actual delegation path.
  For kernel work, follow `dopemux kernel` -> `scripts/taskx` -> `scripts/dopetask` -> external `dopetask`.

- Treat `dopemux` as a coordinator, bootstrap layer, and CLI surface, not as a system of record.

- For PM questions, check whether the action routes to Leantime, task-orchestrator, ConPort, or dope-memory before deciding where truth lives.

- For memory and retrieval questions, assume downstream ownership unless code proves otherwise.

- Mark agent runtime authority as `UNKNOWN` unless a separate canonicality pass proves a single runtime.

- When routing or MCP behavior matters, inspect both command code and the generated config/env surfaces because `dopemux` both launches services and rewrites operator configuration.
