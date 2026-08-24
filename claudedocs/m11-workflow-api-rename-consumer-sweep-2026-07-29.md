---
title: "M11 consumer sweep — task-orchestrator :8000 → dopemux-workflow-api rename"
date: 2026-07-29
status: evidence (supervisor D2 precondition for migration M11, design §10.2)
method: read-only sweep by independent Sonnet agent; DEAD-route claims for /api/pm/* proven by test execution (404)
related: claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md §10.2, rewritten M11
---

# M11 Consumer Sweep — task-orchestrator :8000 → `dopemux-workflow-api`

Scope note up front: two unrelated things share the name "task-orchestrator" in this repo and must not be conflated:

1. **The FastAPI REST service on :8000** (`services/task-orchestrator/app/main.py`, `compose.yml` service `task-orchestrator`) — **this is the M11 rename target**.
2. **The MCP tool wrapper-singleton on :7890** (`mcp_catalog.yaml` entry `task-orchestrator`, `~/.codex/config.toml`, `~/plugins/dopemux-mission-control/.mcp.json`, `mcp-proxy-config.copilot.yaml`, launchd `com.dopemux.mcp-structured-content-proxy.plist`) — an unrelated Kotlin-jar wrapper process. **Out of scope for this rename**; do not touch.

Excluded as false positives (unrelated :8000 uses): `services/dopemux-gpt-researcher/*` (own dev server), `dashboard/service_clients.py:28` (`ADHDEngineClient(base_url="http://localhost:8000")` — misconfigured/stale default that should point at 8095), `.env.example:43` `FRONTEND_API_URL=http://localhost:8000` (same likely-stale dashboard default, UNKNOWN true owner).

## (a) Consumer inventory

| Consumer | How it reaches :8000 | Env var / hardcode | Breakage risk on rename |
|---|---|---|---|
| `src/dopemux/pm/adapters/orchestrator.py:17,103` `TaskOrchestratorAdapter` / `SyncTaskOrchestratorAdapter` | HTTP client, PM-plane canonical reads/writes | `TASK_ORCHESTRATOR_URL` env, default `http://localhost:8000` | HIGH — default breaks if hostname changes and env not repointed |
| `src/dopemux/workflow/service.py:271` `probe_pm_authority()` | GET `/health`, `/api/health` | `DOPEMUX_WORKFLOW_API_URL` env, default `http://localhost:8000` | MEDIUM — env var name already matches the migration target name; likely the intended forward path |
| `src/dopemux/commands/capture_group_commands.py:131-138` `_workflow_api_base_url()` / `_workflow_request()`, used by `src/dopemux/commands/workflow_group_commands.py:280,343,377` (`dopemux workflow` CLI: ideas/epics/promote) | HTTP POST/GET `/api/workflow/ideas`, `/api/workflow/ideas/{id}/promote`, `/api/workflow/epics` | `DOPEMUX_WORKFLOW_API_URL` env, default `http://localhost:8000` | MEDIUM — same forward-looking env var |
| `services/dopecon-bridge/dopecon_bridge/config.py:83-86` `Settings.task_orchestrator_url` | container DNS name | `TASK_ORCHESTRATOR_URL` env, default `f"http://{container_prefix}-task-orchestrator:8000"` | HIGH — the consumer the supervisor doc explicitly names; used by `clients.py:123,136-146` (`health_check_all()` → GET `{url}/health`) and `services/task_integration.py:146,206` |
| `services/adhd_engine/config.py:101` `Settings.task_orchestrator_url` | Docker DNS, bare service name | `TASK_ORCHESTRATOR_URL` env, default `http://task-orchestrator:8000` (bare, no container_prefix) | HIGH — depends on the literal compose/DNS name resolving; breaks silently unless env repointed or alias kept |
| `services/adhd_engine/core/engine.py:84-93` `_resolve_task_orchestrator_url()` | same, settings→env→default fallback chain | same env var / default | HIGH, but has graceful env fallback (tested in `tests/unit/test_adhd_engine_task_orchestrator_url.py`) |
| `services/adhd_engine/core/task_orchestrator_client.py:26,31` | HTTP client default | hardcoded default `http://localhost:8000` | MEDIUM |
| `services/adhd_engine/domains/task_enablement/decomposition_coordinator.py:60`, `task_decomposition_event_listener.py:205` | HTTP client defaults | hardcoded `http://localhost:8000` | MEDIUM |
| `services/dcp-readonly-facade/src/dcp_facade/task_orchestrator.py` + `tools.py:541,567,577,588` | GET `/api/projects/{id}/workflow/{queue,blockers,state}` | `base_url` resolved dynamically from registry (`_profile_binding_url_only`) — actual value UNKNOWN, presumably `services/registry.yaml` (port 8000) at runtime | MEDIUM — runtime registry entry must be updated |
| `services/registry.yaml:152-162` | registry lookup for many consumers (smoke stack, doctor, facade) | `port: 8000`, `compose_service_name: task-orchestrator`, `name: task-orchestrator` | HIGH — canonical registry source; part of rename packet |
| `compose.yml:429-464` | service definition | `container_name: task-orchestrator`, service key `task-orchestrator`, `${TASK_ORCHESTRATOR_PORT:-8000}:8000` | HIGH — the object being renamed |
| `src/dopemux/instance_manager.py:275,301` | multi-instance env computation | sets `TASK_ORCHESTRATOR_PORT` (8000 for instance A, `port_base+14` otherwise) | MEDIUM — value logic tied to compose service (module slated for deletion under design P-04) |
| `src/dopemux/commands/mcp_commands.py:400` | `docker compose --profile manual up -d task-orchestrator` | hardcoded compose service name string | HIGH — literal compose service name in CLI code |
| `.vibe/config.toml:130-139` | operator MCP fleet config | `[[mcp_servers]] name = "task-orchestrator" … url = "http://localhost:8000"` | HIGH — comment already anticipates this rename ("pending rename") |
| `templates/skills/pr-docgen-sync/scripts/pr_docgen_sync_workflow.py:867` + identical copies in `.claude/skills/` and `.github/skills/` | GET `/health`, POST `/api/coordination/operations` | CLI flag `--task-orchestrator-url` default `http://localhost:8000` | MEDIUM — 3 duplicated copies, hardcoded default |
| `tests/unit/test_task_orchestrator_runtime_config.py` | reads/asserts Dockerfile, compose.yml, registry.yaml text | hardcoded literals (`compose["services"]["task-orchestrator"]`, `registry_service["name"]`, port 8000 strings) | HIGH — pinning test; must be updated in the same rename packet |
| `tests/unit/pm/test_pm_route_contracts.py:32,52` | asserts adapter `base_url == "http://localhost:8000"` | hardcoded | MEDIUM |
| `.env.template:25` | doc comment only | `# TASK_ORCHESTRATOR: +14 (3014)` | LOW — stale/contradictory (multi-instance offset scheme, 3014) vs runtime default 8000; cleanup only |
| `.env.example:20` | `TASK_ORCHESTRATOR_API_KEY=...` | key name only, no URL | LOW — cosmetic |

Everything under `mcp_catalog.yaml:390-424`, `~/.codex/config.toml:75-96`, `~/plugins/dopemux-mission-control/.mcp.json:17-18`, `mcp-proxy-config.copilot.yaml:45-46`, `mcp-proxy-config.yaml:28-31` targets port **7890/3017** (the MCP wrapper singleton) — not consumers of the rename target. Launchd: only the 7890/7891 proxy plist; no :8000 references.

## (b) Endpoint classification (`app/main.py` + `app/api/project_workflow.py`)

| Route | Classification | Evidence |
|---|---|---|
| `GET /health` | canonical-workflow (infra) | compose healthcheck (`compose.yml:459-460`), DopeconBridge `health_check_all()`, pr-docgen-sync probe, `.vibe`/workflow_service probe |
| `GET /info` | adapter-proxy / service-discovery | no confirmed in-repo HTTP caller (the :7890 identity probe checks a different port) — candidate for later dead-route review |
| `GET /metrics` | canonical-workflow (infra) | Prometheus format; no in-repo scraper found — UNKNOWN external consumer |
| `POST /api/workflow/ideas` | canonical-workflow | `workflow_group_commands.py:280`, tests |
| `GET /api/workflow/ideas` | canonical-workflow | CLI + tests |
| `PATCH /api/workflow/ideas/{idea_id}` | canonical-workflow (likely) | no non-test caller found — flag for dead-route review |
| `POST /api/workflow/ideas/{idea_id}/promote` | canonical-workflow | `workflow_group_commands.py:343`, tests |
| `POST /api/workflow/epics` | canonical-workflow (likely) | no non-test caller found — flag for dead-route review |
| `GET /api/workflow/epics` | canonical-workflow | `workflow_group_commands.py:377` |
| `PATCH /api/workflow/epics/{epic_id}` | canonical-workflow (likely) | no non-test caller found — flag |
| `GET /api/projects/{id}/workflow/queue` | canonical-workflow | `pm/adapters/orchestrator.py:28`, `dcp_facade/task_orchestrator.py`, `task_integration.py:146` |
| `GET /api/projects/{id}/workflow/blockers` | canonical-workflow | same adapters |
| `GET /api/projects/{id}/workflow/state` | canonical-workflow | same adapters; confirmed live |
| `POST /api/projects/{id}/workflow/transition` | canonical-workflow, **degraded** | called by `orchestrator.py:62,149`; per `docs/03-reference/services/task-orchestrator.md:97,106` returns an explicit unavailable receipt — write authority not yet real. Rename-neutral |
| `POST /api/pm/work-items/{task_id}/update` | **DEAD (proven by execution)** | router in `app/api/pm_tools.py:13,34` never `include_router()`'d in `main.py` (only `project_workflow_router` at `main.py:208`); `pytest services/task-orchestrator/tests/test_pm_tools.py` → both tests 404. Documented as "Active" in `docs/03-reference/services/task-orchestrator.md:50-52` — that doc is wrong |
| `POST /api/pm/work-items/{task_id}/transition` | **DEAD (proven by execution)** | same — 404 |
| `POST /api/pm/work-items/{task_id}/progress` | **DEAD (unmounted, same router)** | same |
| `POST /api/coordination/operations` | adapter-proxy | real caller: pr-docgen-sync workflow script ×3 copies |
| `GET /api/coordination/health`, `GET .../metrics`, `POST .../events`, `GET .../conflicts`, `POST .../conflicts/{id}/resolve`, `GET .../status`, `POST .../test` | **no confirmed caller — DEAD candidates** | repo-wide grep found nothing |
| FastMCP surface (`FastMCP("Task-Orchestrator")`, `main.py:79-98`, 37 tools) | **DEAD (structurally unwired)** | object created, tools registered, but never mounted on the FastAPI app (no `app.mount`, no `mcp.run()`/`sse_app()`); `/info` advertises `"url": ".../sse"` (`main.py:384`) but **no `/sse` route exists** |

## (c) Rename-packet checklist (one bounded packet, behavior preserved)

Identifiers that must change together:
- `compose.yml:430` service key + `:434` `container_name` → `dopemux-workflow-api`
- `services/registry.yaml:152,156` `name` + `compose_service_name`
- `app/main.py:74` `SERVICE_NAME` default; health payload `service=` labels (`main.py:334,343`)
- Prometheus metric prefixes `task_orchestrator_*` (`main.py:413-431`) → `dopemux_workflow_api_*` (supervisor packet text explicitly includes "metrics names")
- `docs/03-reference/services/task-orchestrator.md` + `docs/planes/pm/_evidence/task-orchestrator-runtime-truth/*`
- `src/dopemux/commands/mcp_commands.py:400` literal service name
- `scripts/smoke_up.sh:44` and `scripts/smoke_down.sh:38` smoke-stack service arrays; rename both literals in the same packet, or explicitly retire these active entrypoints before the Compose key changes
- `install.sh:102,238-261` `CORE_STACK_SERVICES` and `stack_services()` filtering; update the literal and add bounded installer coverage proving `--quick` retains the renamed workflow API instead of silently skipping it
- `.github/workflows/containers.yml:64` and `.github/workflows/docker-scout.yml:59` service matrices; update their `task-orchestrator` entries with the Compose key so image build and scan lanes continue to select the service
- `tests/unit/test_task_orchestrator_runtime_config.py` (pinning test — same commit or it fails immediately); `tests/unit/pm/test_pm_route_contracts.py:32,52` if defaults change
- `services/dopecon-bridge/dopecon_bridge/config.py:84` DNS default; `services/adhd_engine/config.py:101` + `core/engine.py:93` bare-DNS default
- `.vibe/config.toml:136-139` entry (already annotated "pending rename")
- **Env var strategy**: keep `TASK_ORCHESTRATOR_URL` as compatibility alias; consolidate on the ALREADY-EXISTING `DOPEMUX_WORKFLOW_API_URL` (used by `workflow/service.py:271`, `capture_group_commands.py:132` with the same default) rather than inventing a third name
- `TASK_ORCHESTRATOR_API_KEY` — naming call only, not functionally required

Migration-window network alias required for: **dopecon-bridge** (container-prefix DNS default) and **adhd_engine** (bare DNS default) — both resolve the literal name; alias must emit a deprecation signal with a removal gate. Env-var-indirected consumers (PM adapter, workflow CLI, facade-via-registry) need no alias.

## (d) DEAD-route evidence (retirement out of scope for the rename; per-route evidence packets later)

1. `/api/pm/work-items/*` — structurally unreachable (router never included); proven by executing `test_pm_tools.py` → 404. Pre-existing bug independent of rename; the reference doc claiming "Active" is wrong.
2. Seven `/api/coordination/*` routes (all but `POST /operations`) — no callers found.
3. `PATCH ideas/{id}`, `POST epics`, `PATCH epics/{id}` — no non-test callers.
4. The FastMCP object + 37 tools — structurally unwired; advertised `/sse` transport does not exist.
5. `GET /info` — no in-repo caller.

## UNKNOWN
- Runtime value of dcp-readonly-facade's registry-bound `base_url` (external runtime registry).
- External Prometheus scrape of `:8000/metrics` (nothing in-repo).
- Out-of-repo processes resolving DNS `task-orchestrator` directly.
- True owner of `.env.example:43` `FRONTEND_API_URL` and `dashboard/service_clients.py:28` default (both look misassigned; ADHD Engine's real port is 8095 per `compose.yml:494`).
