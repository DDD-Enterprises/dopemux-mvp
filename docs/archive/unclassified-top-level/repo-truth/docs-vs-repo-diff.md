---
id: docs-vs-repo-diff
title: Docs Vs Repo Diff
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-31'
last_review: '2026-03-31'
next_review: '2026-06-29'
prelude: Docs Vs Repo Diff (explanation) for dopemux documentation and developer workflows.
---
# DOCS vs Repo Diff

Scope:
- Architecture-affecting docs inspected for this audit, including active docs, service READMEs, MCP docs, and historical docs that still shape architecture understanding.
- Static inspection only. Repo truth is taken from runtime code, config, compose wiring, and canonical PM/MCP modules.

Authority anchors used repeatedly:
- `src/dopemux/pm/models.py`
- `src/dopemux/pm/writes.py`
- `src/dopemux/mcp/registry.yaml`
- `src/dopemux/mcp/resolver.py`
- `src/dopemux/memory/capture_client.py`
- `services/task-orchestrator/app/main.py`
- `services/task-orchestrator/app/api/pm_tools.py`
- `services/task-orchestrator/app/api/project_workflow.py`
- `services/dopecon-bridge/README.md`
- `services/dopecon-bridge/dopecon_bridge/routes.py`
- `services/dopecon-bridge/dopecon_bridge/clients.py`
- `services/working-memory-assistant/dope_memory_main.py`
- `services/working-memory-assistant/main.py`
- `services/working-memory-assistant/canonical_ledger.py`
- `services/working-memory-assistant/chronicle/store.py`
- `services/dope-context/src/mcp/server.py`
- `services/adhd_engine/main.py`
- `services/adhd_engine/api/routes.py`
- `docker/compose.core.yml`

## PM / Task Ownership

| Doc location | Claim | Actual repo truth | Evidence | Mismatch type | Severity |
|---|---|---|---|---|---|
| `README.md` | PM plane authority is simply `Leantime, Task-Master, Task-Orchestrator (task/project authority)`. | Current PM authority is split: canonical lifecycle model in `src/dopemux/pm/models.py`; metadata writes go to Leantime via `pm_update_work_item`; workflow transitions go to Task Orchestrator via `pm_transition_work_item`; progress/decision context goes to ConPort via `pm_log_progress`; dope-memory is the chronicle mirror. Taskmaster is a producer/wrapper, not lifecycle authority. | `src/dopemux/pm/models.py`, `src/dopemux/pm/writes.py`, `services/taskmaster/README.md`, `services/taskmaster/bridge_adapter.py` | missing critical detail | HIGH |
| `services/task-orchestrator/docs/pm-plane-architecture.md` | ConPort is the "storage authority for all project knowledge". | ConPort is only the canonical decision/progress/context authority. PM entities stay in Leantime, workflow authority stays in Task Orchestrator, chronicle memory stays in dope-memory, and retrieval stays in dope-context. | `src/dopemux/pm/writes.py`, `services/working-memory-assistant/dope_memory_main.py`, `services/dope-context/src/mcp/server.py` | incorrect | HIGH |
| `services/task-orchestrator/docs/pm-plane-architecture.md` | Taskmaster AI owns decomposition and next-action logic inside the PM plane. | Workflow legality, blockers, next-action, and transition policy are routed through Task Orchestrator in the PM write layer; Taskmaster is a PM producer/wrapper surface, not the workflow authority. | `src/dopemux/pm/writes.py`, `services/taskmaster/README.md`, `src/dopemux/pm/adapters/core.py` | incorrect | HIGH |
| `services/task-orchestrator/docs/pm-plane-architecture.md` | Canonical MCP/runtime entrypoint is `services/task-orchestrator/server.py`. | Active FastAPI runtime is `services/task-orchestrator/app/main.py`; `services/task-orchestrator/query_server.py` is explicitly unsupported. | `services/task-orchestrator/app/main.py`, `services/task-orchestrator/query_server.py` | incorrect | HIGH |
| `docs/03-reference/services/task-orchestrator.md` | Task Orchestrator scope is mainly idea/epic workflow endpoints. | The runtime also mounts canonical PM write endpoints and workflow state APIs: `app/api/pm_tools.py` and `app/api/project_workflow.py` are included in `app/main.py`. | `services/task-orchestrator/app/main.py`, `services/task-orchestrator/app/api/pm_tools.py`, `services/task-orchestrator/app/api/project_workflow.py` | missing critical detail | MEDIUM |
| `docs/systems/task-orchestrator/coordination.md` | Plane coordinator deploys on port `8090` from the old `docker/mcp-servers` stack. | Canonical compose wiring runs `task-orchestrator` on port `8000`; direct script default inside `app/main.py` is still `3014`; the old `query_server.py` path is unsupported. | `docker/compose.core.yml`, `services/registry.yaml`, `services/task-orchestrator/app/main.py`, `services/task-orchestrator/query_server.py` | outdated | HIGH |
| `docs/archive/history/sourceFiles/docs__90-adr__038-subtask-authority-taskmaster.md` | Task-Master is the authority for subtasks, hierarchy, and next-action. | Current repo PM authority routes lifecycle state through the canonical PM model and workflow transitions through Task Orchestrator, not Task-Master. | `src/dopemux/pm/models.py`, `src/dopemux/pm/writes.py`, `services/task-orchestrator/app/api/project_workflow.py` | outdated | HIGH |

## Memory Authority / ConPort vs dope-query

| Doc location | Claim | Actual repo truth | Evidence | Mismatch type | Severity |
|---|---|---|---|---|---|
| `services/working-memory-assistant/README.md` | `main.py` on port `8096` is the primary working-memory service and API surface. | The canonical deployed memory runtime is `dope_memory_main.py` on port `3020`; `main.py` is a co-located legacy/prototype WMA service. | `services/working-memory-assistant/dope_memory_main.py`, `services/working-memory-assistant/main.py`, `docker/compose.core.yml`, `services/registry.yaml` | incorrect | HIGH |
| `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md` | The first memory plane is "ConPort / DopeQuery". | `services/dope-query` has no repo-proven runtime entrypoint or compose/registry wiring; active authority surfaces are ConPort, dope-memory, and dope-context. | `services/dope-query/auth/models.py`, `services/dope-query/tests/test_password_utils.py`, `src/dopemux/mcp/registry.yaml`, `docker/compose.core.yml` | partially correct | HIGH |
| `docs/04-explanation/technical-deep-dives/dope-memory-deep-dive-2.md` | dope-memory sits beside "DopeQuery (Structural Truth)". | dope-query is not runtime-real in the inspected repo; structural durable context comes through ConPort surfaces, not an active dope-query service. | `services/dope-query/auth/models.py`, `services/dope-query/tests/test_password_utils.py`, `services/dopecon-bridge/dopecon_bridge/clients.py`, `src/dopemux/mcp/registry.yaml` | outdated | HIGH |
| `docs/archive/blueprints/conport-dopemux.md` | ConPort is the central nervous system, including work queue management and unified work items. | Current ConPort surfaces are decision/progress/context oriented. Canonical workflow queue/state APIs live in Task Orchestrator; canonical PM entity updates live in Leantime pathways. | `docker/mcp-servers-source/conport/server.py`, `docker/mcp-servers-source/conport/enhanced_server.py`, `services/task-orchestrator/app/api/project_workflow.py`, `src/dopemux/pm/writes.py` | incorrect | HIGH |
| `docs/archive/history/sourceFiles/docs__rfc__RFC-001-unified-memory-graph.md` | Current memory architecture is ConPort + Milvus + SQL/Neo4j + Zep + Letta. | Current runtime wiring uses Qdrant, ConPort, dope-memory SQLite chronicle, and dope-context. No repo-proven active Zep, Milvus, Neo4j, or Letta runtime was found in the inspected architecture surfaces. | `docker/compose.core.yml`, `services/working-memory-assistant/chronicle/store.py`, `services/working-memory-assistant/canonical_ledger.py`, `services/dope-context/src/mcp/server.py`, `services/dope-query/auth/models.py` | outdated | HIGH |

## Event Architecture / MCP Surfaces

| Doc location | Claim | Actual repo truth | Evidence | Mismatch type | Severity |
|---|---|---|---|---|---|
| `README.md` | "All cross-service communication is event-driven (Redis PubSub)." | The repo uses direct HTTP and MCP calls across major boundaries. Redis exists, but it is not the only or canonical cross-service path. | `services/dopecon-bridge/dopecon_bridge/clients.py`, `services/task-orchestrator/app/main.py`, `src/dopemux/mcp/resolver.py`, `docker/compose.core.yml` | incorrect | HIGH |
| `README.md` | "Service registry and entrypoints are defined in `services/registry.yaml`." | `services/registry.yaml` covers ports/health/config metadata. MCP naming and transports live in `src/dopemux/mcp/registry.yaml`. Runtime entrypoints and commands are split across `compose.yml`, `docker/compose.core.yml`, and each service's `main.py`/wrapper file. | `services/registry.yaml`, `src/dopemux/mcp/registry.yaml`, `compose.yml`, `docker/compose.core.yml`, `services/task-orchestrator/app/main.py`, `services/working-memory-assistant/dope_memory_main.py` | missing critical detail | HIGH |
| `docs/03-reference/mcp-tools-overview.md` | Canonical MCP inventory includes `ddg-mcp`, `conport-admin`, `gptr-researcher-stdio`, and task-orchestrator stdio/on-demand surfaces. | The canonical MCP registry names are the ones in `src/dopemux/mcp/registry.yaml` such as `conport`, `serena`, `desktop-commander`, `gpt-researcher`, `leantime-bridge`, `dopemux-claude-context`, `dope-context`, `pal`, and `dopemux-zen`. | `src/dopemux/mcp/registry.yaml`, `src/dopemux/mcp/resolver.py` | incorrect | HIGH |
| `docs/systems/dope-context/api-reference.md` | "Complete documentation for all 9 MCP tools." | `services/dope-context/src/mcp/server.py` currently registers 18 MCP tools plus custom HTTP routes like `/info`, `/autoindex/bootstrap`, and `/autoindex/status`. | `services/dope-context/src/mcp/server.py` | outdated | HIGH |
| `docs/02-how-to/mcp-service-discovery-guide.md` | `/info` endpoint rollout is only "3/12 complete". | The inspected repo already defines `/info` in additional active surfaces, including Task Orchestrator, dope-context, and Serena's parallel info server. | `services/task-orchestrator/app/main.py`, `services/dope-context/src/mcp/server.py`, `docker/mcp-servers/serena/info_server.py` | outdated | MEDIUM |
| `docs/02-how-to/serena-v2-production-deployment.md` | Serena production runtime is the local `serena.v2.*` implementation with 13 validated components. | Canonical deployed runtime in compose is the wrapper-based MCP surface under `docker/mcp-servers/serena/`; the larger `services/serena/` tree is not the compose authority. | `docker/compose.core.yml`, `docker/mcp-servers/serena/wrapper.py`, `docker/mcp-servers/serena/info_server.py`, `services/serena/mcp_server.py` | incorrect | HIGH |

## System Boundaries / ADHD / Runtime Shape

| Doc location | Claim | Actual repo truth | Evidence | Mismatch type | Severity |
|---|---|---|---|---|---|
| `README.md` | DopeconBridge is the integration gateway for "authority enforcement". | The active bridge is explicitly adapter/proxy only and must not act as canonical task, workflow, decision, or progress authority. | `services/dopecon-bridge/README.md`, `services/dopecon-bridge/dopecon_bridge/routes.py` | incorrect | HIGH |
| `QUICK_START.md` | The `compose.adhd-stack.yml` MVP stack is the practical quick start for current Dopemux runtime understanding. | `compose.adhd-stack.yml` still exists, but canonical installer/runtime selection uses `docker/compose.core.yml` and related overlays; `workspace-watcher`, `activity-capture`, and `adhd-dashboard` are not part of the canonical service registry. | `compose.adhd-stack.yml`, `install.sh`, `docker/compose.core.yml`, `services/registry.yaml` | missing critical detail | MEDIUM |
| `INSTALL.md` | `--stack core|full` selects service profiles inside canonical `compose.yml`. | The installer actually composes fragment stacks: `docker/compose.core.yml`, `docker/compose.pm.yml`, `docker/compose.routing.yml`, `docker/compose.research.yml`, and `docker/compose.agents.yml`. | `install.sh` | incorrect | MEDIUM |
| `INSTALL.md` | Dopemux is TaskX submodule-first via `vendor/taskx`, `scripts/taskx`, and `.taskx-pin`. | Current repo authority is `scripts/dopetask` plus `.dopetask-pin` and `dopetask==0.5.1`; `scripts/taskx` is only a compatibility shim; `vendor/taskx` and `.taskx-pin` are absent. | `scripts/dopetask`, `scripts/taskx`, `.dopetask-pin`, `pyproject.toml` | outdated | MEDIUM |
| `docs/04-explanation/architecture/dopemux-architecture-overview.md` | Core architecture centers on event bus, ChromaDB, Break Suggester, Session Intel, Energy Trends, and similar named services as active runtime building blocks. | Current compose/runtime surfaces center on Qdrant, dope-context, dope-memory, Task Orchestrator, DopeconBridge, ADHD Engine, and wrapper-based Serena. The named services in the doc are not canonical compose/registry services. | `docker/compose.core.yml`, `services/registry.yaml`, `services/dope-context/src/mcp/server.py`, `services/working-memory-assistant/dope_memory_main.py` | outdated | HIGH |
| `services/adhd-dashboard/README.md` | ADHD Dashboard is production, starts from `docker-compose.master.yml`, uses `ADHD_ENGINE_URL=http://localhost:8080`, and exposes trends/break recommendation routes listed in the README. | Backend default is `http://localhost:8095`; the implemented routes include `/api/task-recommendations` and `/api/cognitive-load`, while `/api/analytics/trends` and `/api/breaks/recommendations` are not present in `backend.py`. | `services/adhd-dashboard/backend.py`, `docker/compose.core.yml` | incorrect | HIGH |
| `services/adhd_engine/README.md` | ADHD Engine surface is a broad microservice suite, and core endpoints are exposed as simple `GET /api/v1/energy-level`, `GET /api/v1/attention-state`, `GET /api/v1/cognitive-load`, and `GET /api/v1/break-recommendation`. | Canonical runtime is a single `adhd-engine` service in compose/registry; implemented routes are mounted under `/api/v1`, but several require `/{user_id}` path params and break recommendation is a `POST`. MCP tools are also exposed from `main.py`. | `services/adhd_engine/main.py`, `services/adhd_engine/api/routes.py`, `docker/compose.core.yml`, `services/registry.yaml` | partially correct | MEDIUM |

## Historical Docs

| Doc location | Claim | Actual repo truth | Evidence | Mismatch type | Severity |
|---|---|---|---|---|---|
| `docs/archive/history/sourceFiles/docs__master-architecture.md` | Dopemux is implementation-ready around 64-agent Claude-flow orchestration, Letta + SQLite memory, and unified personal-life automation architecture. | Current repo authority centers on canonical PM writes, ConPort/dope-memory/dope-context separation, compose-wired services, and wrapper-based Serena. The archived architecture does not match current runtime shape. | `src/dopemux/pm/models.py`, `src/dopemux/pm/writes.py`, `services/working-memory-assistant/chronicle/store.py`, `services/dope-context/src/mcp/server.py`, `docker/compose.core.yml` | outdated | HIGH |
| `docs/archive/blueprints/task-orchestrator-dopemux.md` | Task Orchestrator pulls work from a ConPort upcoming queue, executes edits through Morph, validates with Playwright, and runs from `services/task-orchestrator/server.py`. | Current runtime is `app/main.py`; workflow APIs are mounted from `app/api`; ConPort is not the canonical workflow queue authority, and no active Task Orchestrator runtime surface in the inspected repo owns a Morph/Playwright execution loop. | `services/task-orchestrator/app/main.py`, `services/task-orchestrator/app/api/project_workflow.py`, `services/dopecon-bridge/dopecon_bridge/clients.py`, `docker/compose.core.yml` | outdated | HIGH |
| `docs/archive/blueprints/conport-dopemux.md` | ConPort owns work queue management, status synchronization, and central execution memory. | Current split is Leantime for PM records, Task Orchestrator for workflow, ConPort for decision/progress/context, and dope-memory for chronicle memory. | `src/dopemux/pm/writes.py`, `services/dopecon-bridge/README.md`, `services/working-memory-assistant/dope_memory_main.py` | outdated | HIGH |
| `docs/archive/history/sourceFiles/docs__90-adr__038-subtask-authority-taskmaster.md` | Task-Master owns next-action and hierarchy for the current architecture. | Current PM stack routes next-action/workflow state through Task Orchestrator and canonical PM model boundaries, not historical Task-Master-first authority. | `src/dopemux/pm/models.py`, `src/dopemux/pm/writes.py`, `services/task-orchestrator/app/api/project_workflow.py` | outdated | HIGH |

## Audit Summary

Highest-impact drift classes found:
- PM/workflow authority is repeatedly flattened into older "Leantime + Taskmaster + ConPort" narratives.
- Memory docs still leak `DopeQuery` or older unified-memory concepts into the active architecture, even though the current repo runtime separates ConPort, dope-memory, and dope-context.
- MCP inventories and service-discovery docs are behind the current registry and tool surfaces.
- Historical docs are still precise enough to mislead architecture readers unless they are explicitly treated as archival only.
