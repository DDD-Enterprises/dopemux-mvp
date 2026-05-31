# TASK_ORCH_MCP_PLUGIN_SURFACE

Safety audit of every MCP, plugin, hook, event, workflow, and coordination surface relevant to integrating `task-orchestrator` into Dopemux daily operator workflows.

Every claim cites file:line. Mutation surfaces are tiered T0–T6; `TX` / `TU` mark surfaces the audit cannot classify with confidence (refuse / route to human). `UNKNOWN` and `CONFLICTING` preserved per [AGENTS.md §2](AGENTS.md) Truth Order.

Generated: 2026-05-25. HEAD: `7037c5f29df11ca3fec55f991a4805e86e997e1e`. Companion to [TASK_ORCH_INTEGRATION_REPO_INVENTORY.md](TASK_ORCH_INTEGRATION_REPO_INVENTORY.md).

---

## Executive summary (read first)

**The most consequential fact in this audit**: the task-orchestrator MCP surface Claude is *actually using right now in this session* (v3, 13 tools: `manage_items`, `query_items`, `manage_notes`, `query_notes`, `manage_dependencies`, `query_dependencies`, `advance_item`, `get_next_status`, `get_next_item`, `get_blocked_items`, `complete_tree`, `create_work_tree`, `get_context`) is **not source-verifiable from this repo**. `grep -rn "manage_items\|advance_item\|complete_tree" services/task-orchestrator/` returns zero matches. The in-repo task-orchestrator at `services/task-orchestrator/` exposes a *different* 6-tool MCP set (`analyze_dependencies`, `batch_tasks`, `get_adhd_state`, `get_task_recommendations`, `record_break`, `get_agent_status`) plus a FastAPI workflow service at port 8000. Every tier in the table below for the v3 surface is **TX** until its source is identified.

Three other findings should shape any integration decision:

1. **Dangerous mode is partially enforced — inverse-failure risk on 3 of 5 vars.** [src/dopemux/cli.py#L3771-L3779 + L5752-L5757](src/dopemux/cli.py#L3771) SETS 5 env vars. Of those, **2 are consumed in-repo** by [src/dopemux/claude/launcher.py#L181-L189](src/dopemux/claude/launcher.py#L181-L189) (`CLAUDE_CODE_SKIP_PERMISSIONS` and `DOPEMUX_DANGEROUS_MODE` → appends `--dangerously-skip-permissions` to the `claude` argv). The other **3 vars (`HOOKS_ENABLE_ADAPTIVE_SECURITY`, `METAMCP_ROLE_ENFORCEMENT`, `METAMCP_APPROVAL_REQUIRED`) are NOT consumed anywhere** in `src/`, `services/`, or `scripts/` — only the launcher gate at L181-L189 plus a child-env propagation at L373 read any of these vars. The 3 unconsumed vars' enforcement (if any) lives in an external MetaMCP layer (UNKNOWN in this repo). **If MetaMCP is not loaded or not configured to consume them, the operator-visible MetaMCP/hook-adaptive-security guards advertised by `/dangerous` are a no-op while the operator believes those guards are disabled** — inverse-failure mode confined to the 3 unconsumed vars.
2. **`dope-context.clear_index` is T6 destructive with no guard** ([server.py:1586](services/dope-context/src/mcp/server.py#L1586)). Wipes all Qdrant collections for the workspace; no recovery.
3. **Implicit automation triggers T4–T5 mutations without operator approval**: SPRINT_STARTED auto-decomposition, `.claude/CLAUDE.md` auto-rewrite, context auto-save on CONTEXT_SWITCH heuristic. Any new operator-facing surface must not mirror these auto-trigger patterns.

---

## Tier System (used throughout)

- **T0** — read-only status (no side effects)
- **T1** — local analysis (compute only; no persisted writes)
- **T2** — draft artifact creation (local file in `claudedocs/` / `out/`, not runtime state)
- **T3** — repo-local non-runtime docs edits (writes `.md` in repo tree)
- **T4** — source/config/test edits (runtime code, settings, schemas, tests)
- **T5** — GitHub mutation (`gh pr create`, comment, label, merge)
- **T6** — deploy/release/destructive (docker prune, db drop, force-push, `clear_index`)
- **TX** — unknown, refuse (insufficient evidence to tier; route to human)
- **TU** — unclassified, refuse (tool exists but behavior opaque; route to human)

Default policy proposal (Section 6): task-orchestrator auto-invoke whitelist = T0/T1 only; everything ≥T2 must traverse an explicit operator approval gate.

---

## 1. MCP Servers

> **Critical disambiguation**: The current Claude session has **two task-orchestrator surfaces** loaded:
> 1. **In-repo, port 8000** — `services/task-orchestrator/app/main.py` (FastAPI) + `task_orchestrator/mcp/__init__.py` (6-tool stdio MCP). This is what compose.yml builds.
> 2. **External "v3 MCP Task Orchestrator" — 13 tools** (manage_items, query_items, manage_notes, query_notes, manage_dependencies, query_dependencies, advance_item, get_next_status, get_next_item, get_blocked_items, complete_tree, create_work_tree, get_context). Per system-reminder text. **Not in this repo** — `grep -rn "manage_items\|advance_item\|complete_tree" services/task-orchestrator/` returns nothing. Loaded via `mcp-proxy-config*`.
>
> Similarly, ConPort has multiple surfaces: (a) `docker/mcp-servers/conport/server.py` (13 tools, local), (b) user-side `mcp__conport__*` tools from upstream ConPort (richer set: semantic_search_conport, batch_log_items, link_conport_items, log_system_pattern, …), (c) `src/conport/memory_server.py` (third variant: unified memory graph with Milvus+Postgres, exposes `mem.*` / `graph.*`).

| Server | Entrypoint | Tool Names | Transport | Read/Write | Approval Tier | Evidence |
|---|---|---|---|---|---|---|
| **task-orchestrator (in-repo)** | [services/task-orchestrator/task_orchestrator/mcp/__init__.py](services/task-orchestrator/task_orchestrator/mcp/__init__.py) (6 tools); FastMCP constructed at [app/main.py#L79](services/task-orchestrator/app/main.py#L79) and tools registered at [L82-L98](services/task-orchestrator/app/main.py#L82-L98) | `analyze_dependencies`, `batch_tasks`, `get_adhd_state`, `get_task_recommendations`, `record_break`, `get_agent_status` | **stdio only via [mcp_stdio.py](services/task-orchestrator/mcp_stdio.py)** (`mcp.run(transport="stdio")`, replaces uvicorn). The `/info` endpoint at [app/main.py#L350-L377](services/task-orchestrator/app/main.py#L350-L377) advertises `mcp.connection.url=http://localhost:{port}/sse` but **no `/sse` route is ever mounted** — the FastAPI app never calls `app.mount("/sse", mcp.sse_app())` so that URL 404s when uvicorn is the entrypoint. To make SSE real, either add an `app.mount` before `uvicorn.run` or change `mcp_stdio.py` to `mcp.run(transport="sse")`. | mixed | `analyze_dependencies`/`get_adhd_state`/`get_task_recommendations`/`get_agent_status` T0; `batch_tasks` T1 (compute-only batching, returns synchronously, no persistence); `record_break` T1 (mutates in-process `adhd_monitor` state, not durable) | mcp/__init__.py:22-106; FastMCP at app/main.py#L79; `/info` at app/main.py#L350-L377 (advertised but not mounted); repo grep for `mount\|sse_app\|mcp.run` in `services/task-orchestrator/*.py` returns zero matches for any SSE wiring |
| **task-orchestrator (external v3)** | UNKNOWN — referenced by system-reminder; loaded via [mcp-proxy-config.yaml](mcp-proxy-config.yaml) | `manage_items`, `query_items`, `manage_notes`, `query_notes`, `manage_dependencies`, `query_dependencies`, `advance_item`, `get_next_status`, `get_next_item`, `get_blocked_items`, `complete_tree`, `create_work_tree`, `get_context` | UNKNOWN (likely stdio via proxy) | unverifiable | **TX — source not in repo; every tier in this row is inferred from tool name only**. Inferred only: `query_*`/`get_*` look T0; `manage_*`/`advance_item`/`complete_tree`/`create_work_tree` look T4; no approval guards observable | system-reminder MCP instructions; mcp-proxy-config*; source absent from `services/task-orchestrator/` (verified via grep) |
| **ConPort (in-repo docker)** | [docker/mcp-servers/conport/server.py](docker/mcp-servers/conport/server.py) lines 35–164 | `get_progress` (36), `update_progress` (47), `get_decisions` (55), `log_decision` (66), `get_recent_activity` (82), `get_active_work` (91), `workspace_summary` (100), `fork_instance` (109), `promote` (120), `promote_all` (127), `get_context` (134), `update_context` (143), `log_progress` (151) | stdio (per docker MCP container conventions) | mixed | reads T0; writes T4; `promote_all` T5 (batch state propagation); `fork_instance` T4–T5 | server.py with `@mcp.tool()` decorator on each |
| **ConPort (external/upstream)** | UNKNOWN — loaded by Claude session via mcp-proxy or settings.local.json | `log_decision`, `log_progress`, `get_active_context`, `update_active_context`, `log_system_pattern`, `log_custom_data`, `link_conport_items`, `semantic_search_conport`, `batch_log_items`, `delete_decision_by_id`, `delete_system_pattern_by_id`, `delete_progress_by_id`, `delete_custom_data`, `search_decisions_fts`, `search_custom_data_value_fts`, … | UNKNOWN | mixed | reads T0; writes T4; `delete_*` T5 (irreversible) | user-loaded ConPort tool list (visible to Claude session); **TX for tools without source path in this repo** |
| **ConPort (unified memory variant)** | [src/conport/memory_server.py](src/conport/memory_server.py) | `mem.upsert`, `mem.search`, `graph.link`, `graph.neighbors` (per docstring lines 1–10) | stdio (`stdio_server` import line 30) | mixed | reads T0; writes T4 (Milvus + PG persistence) | memory_server.py header docstring + imports |
| **PAL** | [docker/mcp-servers/pal/](docker/mcp-servers/pal/) (external `pal-mcp-server` package) | `chat`, `thinkdeep`, `planner`, `consensus`, `debug`, `codereview`, `challenge`, `analyze`, `refactor`, `secaudit`, `testgen`, `tracer`, `docgen`, `precommit`, `version`, `listmodels`, `clink`, `apilookup` | HTTP (port 3003) + stdio in some contexts | analytical-read | T1 for all (multi-model reasoning; no repo mutation); `precommit` reads diff only | docker/mcp-servers/SERVER_REGISTRY.md; .claude/MCP_PAL.md (autoloaded) |
| **Serena** | [docker/mcp-servers/serena/](docker/mcp-servers/serena/) | LSP-based: code navigation, complexity scoring, semantic search, find_test_file, predict_navigation_from_git, find_similar_code | stdio + HTTP (port 4006) | read-only | T0/T1 (read-only LSP + analysis) | docker/mcp-servers/serena/; .claude/MCP_Serena.md |
| **dope-context** | [services/dope-context/src/mcp/server.py](services/dope-context/src/mcp/server.py) | `search_code` (1363), `docs_search` (1831), `search_all` (2178), `index_workspace` (992), `index_docs`, `sync_workspace` (2418), `sync_docs` (2496), `start_autonomous_indexing` (2636), `stop_autonomous_indexing` (2688), `start_autonomous_docs_indexing` (2876), `stop_autonomous_docs_indexing` (2928), `configure_decision_auto_indexing` (2019), `get_index_status` (1507), `get_search_metrics` (2535), `clear_search_metrics` (2561), `get_autonomous_status` (2748), `get_chunk_complexity` (2991), `clear_index` (1586) | HTTP (port 3010) | mixed | searches T0/T1; index/sync T4; **`clear_index` T6 (destructive, no recovery)** | server.py line numbers per agent inventory |
| **GPT Researcher (gptr-mcp)** | [docker/mcp-servers/gptr-mcp/](docker/mcp-servers/gptr-mcp/) | `deep_research`, `quick_search`, `write_report`, `get_research_sources`, `get_research_context` | HTTP (port 3009) | read | T1 (external web research; writes to local report files = T2 for write_report) | .claude/MCP_GPTResearcher.md |
| **Exa** | [docker/mcp-servers/exa/exa_server.py](docker/mcp-servers/exa/exa_server.py) lines 95–317 | `search_web` (96), `get_contents` (182), `search_and_contents` (239), `find_similar` (317) | HTTP (port 3011) | read | T0 (all read-only external API) | exa_server.py |
| **Desktop Commander** | [docker/mcp-servers/desktop-commander/server.py](docker/mcp-servers/desktop-commander/server.py) lines 38–102 | `screenshot` (39), `window_list` (60), `focus_window` (74), `type_text` (102) | stdio + HTTP (3012) | mixed | `screenshot`/`window_list` T0; **`focus_window`/`type_text` T4 (modify foreign-app state; can hit any open document)** | server.py |
| **Leantime Bridge (MCP)** | [docker/mcp-servers/leantime-bridge/leantime_bridge/server.py](docker/mcp-servers/leantime-bridge/leantime_bridge/server.py) | NOT fully enumerated in audit window; JSON-RPC client to external Leantime API | stdio + HTTP (3015) | mixed | **TU** for unenumerated tools | server.py lines 1–100+ (token-truncation observed); tool list opaque without deeper read |
| **LiteLLM** | [docker/mcp-servers/litellm/](docker/mcp-servers/litellm/) | none — transparent LLM HTTP proxy, not an MCP server | HTTP (port 4000) | N/A | N/A | infrastructure only |
| **dopecon-bridge** | [services/dopecon-bridge/main.py](services/dopecon-bridge/main.py); routes in [dopecon_bridge/routes.py](services/dopecon-bridge/dopecon_bridge/routes.py) | **NOT MCP** — pure HTTP REST. Includes `/auth/*`, `/events/*`, `/tasks/*`, `/kg/{decisions,custom_data,progress}`, `/route/pm`, `/ddg/*`, `/health` | HTTP (port 3016) | mixed | reads T0; PM-routed writes T4–T5; **`/route/pm` checks `WORKFLOW_SIGNIFICANT_OPERATIONS` (routes.py:34–43, 145–151) but does NOT hard-block — gate is advisory** | routes.py |

---

## 2. MCP Tool Registry Candidates

> **Per spec**: "Do not design new tools yet. Inventory what exists and identify gaps."

For each candidate tool family the user proposed for task-orchestrator, identify which existing runtime paths cover the function, what's missing, and the safety risk if task-orchestrator wraps them naively.

| Candidate Tool Family | Existing Runtime Support? | Existing Paths | Missing Pieces | Risk |
|---|---|---|---|---|
| **orchestrator.status.*** (workflow state read) | **YES — strong** | `GET /api/projects/{id}/workflow/queue`, `/blockers`, `/state` in [app/api/project_workflow.py](services/task-orchestrator/app/api/project_workflow.py); wrapped by [src/dopemux/pm/adapters/orchestrator.py:10+](src/dopemux/pm/adapters/orchestrator.py#L10) `TaskOrchestratorAdapter.get_queue/get_blockers/get_state` | No MCP wrapper around these read APIs (only HTTP); no slash command surface | LOW (T0 reads only) — main risk is latency under load; adapter timeout is 10s |
| **orchestrator.plan.*** (decompose / sequence) | **PARTIAL** | `task_decomposition_endpoint.py` (12.5 KB; bundled in Dockerfile line 23 but not registered in app/main.py); `automation_workflows.py auto_sprint_planning` workflow (lines 125–147) | No operator-facing "plan this packet" tool; decomposition currently auto-fires on SPRINT_STARTED with no approval | MED — auto-decomposition mutates ConPort tasks (T4); manual surface needed |
| **orchestrator.packet.*** (task packet CRUD + validation) | **YES (validation) / NO (orchestrator-side CRUD)** | Schema at [docs/03-reference/spec/dopetask/dopetask-canonical-spec.json](docs/03-reference/spec/dopetask/dopetask-canonical-spec.json); validation invoked via `python -m jsonschema -i <tp> docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` (per PROOF.json patterns) | No task-orchestrator endpoint that ingests, persists, or executes packets directly. Packets live under `task-packets/generated/` and `proof/.../PROOF.json` files | HIGH (gap) — task-orchestrator is workflow-transition authority per AGENTS.md §6 but packet-lifecycle authority is UNKNOWN/dopetask-adjacent |
| **orchestrator.review.*** (PR / codereview hooks) | **PARTIAL** | PAL provides `codereview` MCP tool (T1 analysis); `/api/coordination/events` can emit review events; .github/workflows/preflight.yml runs in CI | No native review-orchestration endpoint in task-orchestrator; review is operator-driven via `gh pr` or PAL | MED — wiring PAL→task-orch→ConPort review-trail is the integration gap [DOPETASK_INTEGRATION_ANALYSIS.md](DOPETASK_INTEGRATION_ANALYSIS.md) names |
| **orchestrator.route.*** (cross-plane routing) | **YES** | dopecon-bridge `/route/pm` (routes.py:128, with policy check at 145–149); task-orchestrator `/api/coordination/*` family (8 routes); event emission to bridge | route via bridge is advisory (not hard-blocking); no MCP wrapper | MED — bridge handler creep is named DANGER in [AGENTS.md §10](AGENTS.md) |
| **orchestrator.memory.*** (decisions, progress, chronicle) | **YES (via wrapping)** | [src/dopemux/pm/writes.py](src/dopemux/pm/writes.py) `pm_log_progress` → ConPort + dope-memory mirror; `pm_log_decision` → ConPort | No task-orchestrator MCP tool for these — callers go through `src/dopemux/pm` library or ConPort/dope-memory MCPs directly | LOW — wrapping is straightforward but should preserve canonical-writer routing |
| **orchestrator.proof.*** (proof bundle assembly + validation) | **PARTIAL — schemas exist; assembly is manual** | Two templates: comprehensive [docs/03-reference/fast-dev-os/templates-proof/proof-bundle-template.json](docs/03-reference/fast-dev-os/templates-proof/proof-bundle-template.json) and minimal [docs/03-reference/governance/codex-proof-template.json](docs/03-reference/governance/codex-proof-template.json); RTE prescan receipt is third schema | No assembler service; no validator-on-save; no canonical receipt store. RTE proofs follow yet another schema | HIGH — proof regime is mandated by [AGENTS.md §9](AGENTS.md) but enforcement is informal |
| **orchestrator.github.*** (gh PR/issue/check) | **PARTIAL** | `dopemux-pr-merge` CLI ([pyproject.toml:139](pyproject.toml)); `dopemux-github` CLI; gh CLI invoked from PROOF bundles; .github/workflows/preflight + codeql + gemini-scheduled-triage | No task-orchestrator wrapper; gemini-scheduled-triage auto-comments on PRs (T6) | HIGH (T5/T6 reach) — must require operator approval before any wrapper |
| **orchestrator.daily.*** (operator startup orientation) | **PARTIAL** | `.claude/commands/save.md`; session_lifecycle.py SessionStart restores ConPort context; no equivalent for "what's in my queue / what's blocked" | No slash command surface combining workflow queue + blockers + progress + ConPort active_context | MED — read-only enhancement; main risk is adapter timeout at SessionStart |

---

## 3. Existing Hooks / Event Surfaces

| Surface | Trigger | Handler | Mutates? | Receipt? | Failure Behavior | Evidence |
|---|---|---|---|---|---|---|
| `check_energy.sh` | PreToolUse | curl to ADHD Engine `/state`; warns if low | no | stdout log line | exits 0 (allows tool) | [.claude/hooks/check_energy.sh:23–26](.claude/hooks/check_energy.sh#L23) |
| `log_progress.sh` | PostToolUse | fire-and-forget curl to `/record-progress` | no (event fire) | none — backgrounded | exits 0 always | [.claude/hooks/log_progress.sh:13–18](.claude/hooks/log_progress.sh#L13) |
| `save_context.sh` | PostToolUse, PreCompact, SessionEnd | fire-and-forget curl to `/save-context` | yes (ConPort context write via ADHD engine) | none surfaced to caller | exits 0 always | [.claude/hooks/save_context.sh:16–21](.claude/hooks/save_context.sh#L16) |
| `track_file_edit.sh` | PostToolUse (edit tools) | curl orchestrator `/track_edit` with file path | yes (tracking event log) | none | exits 0 | [.claude/hooks/track_file_edit.sh:16–18](.claude/hooks/track_file_edit.sh#L16) |
| `prompt_analyzer.py` | UserPromptSubmit, PreToolUse | analyzes prompt → POSTs `/log-intent`, `/save-context`, `/record_intent`; injects context into prompt | yes (intent log + context write) | JSON stdout with `contextInjection` field | exits 0 on error (silent fail) | [.claude/hooks/prompt_analyzer.py:298–361](.claude/hooks/prompt_analyzer.py#L298) |
| `session_lifecycle.py` | SessionStart, SessionEnd, Stop | calls orchestrator `/start_session` / `/end_session`; reads/writes `/tmp/dopemux_current_session.json` | yes (filesystem state file) | async result optionally displayed | swallows exceptions silently | [.claude/hooks/session_lifecycle.py:23–57](.claude/hooks/session_lifecycle.py#L23) |
| `native_hooks.py` dispatcher | **all 10 lifecycle events** | unified Python dispatcher; routes to per-event handlers; manages WorkflowKernel state | yes (workflow state via `kernel.save(state)`) | system message + additional_context | **CAN BLOCK** with `EXIT_BLOCK=2` for iteration/time/safe-stop violations | [src/dopemux/claude/native_hooks.py:144–369](src/dopemux/claude/native_hooks.py#L144) |
| `_on_pre_tool_use` | PreToolUse | checks `max_iterations` + `max_minutes`; records attempt | yes (tool_event record) | event record | **BLOCKS** if limits exceeded | [native_hooks.py:196–227](src/dopemux/claude/native_hooks.py#L196) |
| `_on_permission_request` | PermissionRequest | auto-allows safe-tool allowlist `{read_file, glob, list_dir, search_file_content}`; routes others to operator | no | allow/deny decision | denies unknown tools | [native_hooks.py:229–246](src/dopemux/claude/native_hooks.py#L229) |
| `_on_stop` | Stop, SubagentStop | validates checkpoint + completion-token; checks safe-stop | yes (state update) | state checkpoint | **BLOCKS** stop with EXIT_BLOCK if not safe-stop | [native_hooks.py:282–313](src/dopemux/claude/native_hooks.py#L282) |
| `.githooks/pre-commit` | git pre-commit | runs `scripts/repo_preflight.sh` + `scripts/preflight.sh RUN_MODE=enforce` | yes (commit block) | preflight log | fails commit if preflight fails | [.githooks/pre-commit:5–8](.githooks/pre-commit#L5) |
| `.github/workflows/preflight.yml` | push to PR / dispatch | preflight enforce mode again | yes (CI status) | check-run | fails check | [.github/workflows/preflight.yml](.github/workflows/preflight.yml) |
| `.github/workflows/codeql.yml` | push | code scan only | no | check-run | none — analysis only | [.github/workflows/codeql.yml](.github/workflows/codeql.yml) |
| `.github/workflows/gemini-scheduled-triage.yml` (this job only) | cron hourly + workflow_dispatch | reads issues/PRs; outputs `triaged_issues` | **NO (permissions: issues:read, pull-requests:read)** | env var output for downstream consumer | no human-in-loop within this job | [.github/workflows/gemini-scheduled-triage.yml](.github/workflows/gemini-scheduled-triage.yml) lines 30–45 (permissions block) |
| **EventCoordinator** (task-orchestrator) | 13 event types: TASK_CREATED, TASK_UPDATED, TASK_COMPLETED, SPRINT_STARTED, SPRINT_ENDED, BREAK_NEEDED, CONTEXT_SWITCH, FOCUS_MODE_CHANGED, ENERGY_LEVEL_CHANGED, SYNC_REQUIRED, CONFLICT_DETECTED, AUTOMATION_TRIGGERED | 9 async workers across priority tiers | yes (cascading event emission; downstream mutations) | Redis DB 3 history (lpush/ltrim, 7-day TTL) | retry with exponential backoff; fire-and-forget | [services/task-orchestrator/event_coordinator.py:161–508](services/task-orchestrator/event_coordinator.py#L161) |
| **ImplicitAutomationEngine** | 4 workflows: `auto_sprint_planning`, `auto_progress_tracking`, `auto_retrospective`, `auto_context_management` | conditions-only triggers (no approval) | yes (ConPort, Leantime, .claude/CLAUDE.md regeneration) | event log only | fire-and-forget; cognitive-load defer (5 min) | [services/task-orchestrator/automation_workflows.py:125–282](services/task-orchestrator/automation_workflows.py#L125) |
| **dopecon-bridge `/events/publish`** | HTTP POST | Redis Stream publish | yes (event emitted to bus) | response receipt | none | [services/dopecon-bridge/dopecon_bridge/routes.py:125](services/dopecon-bridge/dopecon_bridge/routes.py#L125) |
| **WebSocket `/ws/coordination`** | task-orchestrator runtime | broadcasts coordination events | yes (broadcast all connected clients) | none | none | [services/task-orchestrator/app/main.py:731–789](services/task-orchestrator/app/main.py#L731) |

---

## 4. Mutation Surfaces

| Surface | Mutation Type | Canonical Writer? | Approval Tier | Current Guard | Missing Guard | Evidence |
|---|---|---|---|---|---|---|
| **`POST /api/pm/work-items/{id}/transition`** | workflow transition (state change) | **YES** — task-orchestrator per [AGENTS.md §6 line 80](AGENTS.md) | T4 | optimistic-concurrency `expected_version`; idempotency_key | no operator confirmation gate | [src/dopemux/pm/writes.py:243–284](src/dopemux/pm/writes.py#L243) |
| **`POST /api/projects/{id}/workflow/transition`** | project-scoped workflow transition | same as above | T4 | same | same | [services/task-orchestrator/app/api/project_workflow.py:442–451](services/task-orchestrator/app/api/project_workflow.py#L442) |
| **`POST /api/workflow/ideas`** + epics endpoints | workflow records create/update/promote | NO — task-orchestrator routes through DopeconBridge custom-data categories `workflow_ideas`/`workflow_epics`/`workflow_audit` | T4 | none observable; relies on bridge custom-data ACL | no schema enforcement at HTTP layer | [services/task-orchestrator/app/main.py:441–546](services/task-orchestrator/app/main.py#L441); [PM_PLANE.md §5.4](PM_PLANE.md) |
| **ConPort `log_decision` / `update_progress` / `log_progress`** | structured decisions, progress | YES — ConPort | T4 | none — bare write | no per-decision approval | [docker/mcp-servers/conport/server.py:47,66,151](docker/mcp-servers/conport/server.py#L47) |
| **ConPort `promote` / `promote_all`** | promote instance-local → shared | YES | **T5** (batch state propagation) | none | no batch confirmation; `promote_all` is unbounded | [conport/server.py:120,127](docker/mcp-servers/conport/server.py#L120) |
| **ConPort `fork_instance`** | clone instance state to new instance | YES | T4 (potentially T5 if cross-workspace) | none | no source/target validation visible | [conport/server.py:109](docker/mcp-servers/conport/server.py#L109) |
| **ConPort upstream `delete_decision_by_id` / `delete_progress_by_id` / `delete_custom_data` / `delete_system_pattern_by_id`** | irreversible deletion | YES | **T5** (irreversible) | none surfaced | no soft-delete / no "type confirmation" pattern | user-loaded ConPort tool list |
| **dopecon-bridge `/kg/decisions` POST** | ConPort decision proxy | proxy only (not canonical writer) | T4 | `X-Source-Plane` header validation (kg_authority.py:71); 403 on mismatch | actual decision validity not checked | [services/dopecon-bridge/dopecon_bridge/routes.py](services/dopecon-bridge/dopecon_bridge/routes.py) |
| **dopecon-bridge `/kg/progress` POST** | ConPort progress proxy | proxy only | T4 | source-plane validation | same | routes.py |
| **dopecon-bridge `/kg/custom_data` POST** | ConPort custom-data proxy (including workflow_*) | proxy only | T4 | source-plane validation | same | routes.py |
| **dopecon-bridge `/route/pm` POST** | PM operation router (delegates to Leantime/task-orch/etc.) | proxy only | T4–T5 | `WORKFLOW_SIGNIFICANT_OPERATIONS` check (routes.py:34–43 + 145–151) is **advisory** — does NOT hard-block | enforcement is "fail closed" claim per legacy comment but observably soft | routes.py |
| **dope-memory `append_chronicle`** | chronicle/receipt | YES — dope-memory | T4 | none | mirror failure → silent (per writes.py:324: receipt succeeds anyway) | [src/dopemux/pm/writes.py:318–325](src/dopemux/pm/writes.py#L318); [services/working-memory-assistant/dope_memory_main.py](services/working-memory-assistant/dope_memory_main.py) |
| **dope-context `index_workspace` / `sync_workspace` / `sync_docs`** | rebuild/update Qdrant vectors | YES — dope-context | T4 | none | long-running; can saturate Qdrant | [services/dope-context/src/mcp/server.py:992,2418,2496](services/dope-context/src/mcp/server.py#L992) |
| **dope-context `start_autonomous_indexing` / `stop_autonomous_indexing`** | background worker control | YES | T4 | none | no graceful-stop protection mid-sync | server.py:2636,2688 |
| **dope-context `clear_index`** | **delete all collections** | YES | **T6 — destructive, no recovery** | none | no confirmation; no quarantine | [server.py:1586](services/dope-context/src/mcp/server.py#L1586) |
| **dope-context `configure_decision_auto_indexing`** | affects cross-plane decision retrieval limits | YES | T4 | none observable | mutates "TRINITY_BOUNDARY_MARKER" defaults (limit 3, max 10) | server.py:2019 |
| **Leantime via `pm_update_work_item`** | passive PM metadata (title, assignee, dates, labels) | YES — Leantime | T4 | rejects workflow-significant fields; fail-closed if client missing; idempotency_key | none beyond canonical-writer routing | [src/dopemux/pm/writes.py:196–240](src/dopemux/pm/writes.py#L196) |
| **WebSocket `/ws/coordination` broadcast** | broadcasts coordination events to all connected clients (runtime state reaching arbitrary subscribers) | task-orchestrator runtime | T4 (runtime state mutation reaching arbitrary connected clients — not an artifact) | none | no per-message ACL; no subscriber authentication observable | [services/task-orchestrator/app/main.py:731–789](services/task-orchestrator/app/main.py#L731) |
| **EventCoordinator `_process_*` handlers** | downstream mutations (auto-decompose, ConPort context, Claude.md regeneration) | varies | T4–T5 | ADHD cognitive-load filter (heuristic only) | **NO user approval** for auto-decompose on SPRINT_STARTED | [event_coordinator.py:370–508](services/task-orchestrator/event_coordinator.py#L370) |
| **EventCoordinator auto-update of `.claude/CLAUDE.md`** | regenerates repo doc on SPRINT_STARTED | NO — automation, not authoritative writer | **T4** (silently mutates committed doc) | none | no version-control check; no operator notification | [event_coordinator.py:444](services/task-orchestrator/event_coordinator.py#L444) — `update_claude_context_for_sprint` |
| **`native_hooks.py` `_on_user_prompt` / `_on_pre/post_tool_use`** | workflow kernel state (iteration count, tool history) | YES — WorkflowKernel | T4 (file-based state) | iteration/time limits | no audit log of state mutations | [native_hooks.py:180–280](src/dopemux/claude/native_hooks.py#L180) |
| **`.githooks/pre-commit` enforce mode** | blocks git commit | YES — preflight | T4 (developer machine) | exit-code check | no descriptive error to dev before fail | [.githooks/pre-commit:5–8](.githooks/pre-commit#L5) |
| **`.github/workflows/gemini-scheduled-triage.yml`** (this job only) | reads issues/PRs and outputs `triaged_issues` env var; runs hourly cron | NO | **T0 at this job's permissions**: `permissions: {contents: read, id-token: write, issues: read, pull-requests: read}` (line ~38). No write permission to issues or PRs in this job. | GitHub-native permissions block (workflow cannot mutate beyond what is granted) | downstream consumer of `triaged_issues` output may be T5 — **REQUIRES_REPO_INSPECTION** of any follow-on job/workflow that mutates based on this output | [.github/workflows/gemini-scheduled-triage.yml](.github/workflows/gemini-scheduled-triage.yml) lines 30–45 (permissions block) |
| **`/tmp/dopemux_current_session.json` (session file)** | session state file | session_lifecycle.py | T4 (filesystem; lives in /tmp) | none | no lock; concurrent writes can race | [.claude/hooks/session_lifecycle.py:45,280](.claude/hooks/session_lifecycle.py#L45) |
| **`Desktop Commander.focus_window` / `.type_text`** | foreign-app UI mutation | NO — alien process | **T4** (can modify any open document/form) | none | no operator approval | [docker/mcp-servers/desktop-commander/server.py:74,102](docker/mcp-servers/desktop-commander/server.py#L74) |

---

## 5. Receipt / Proof Surfaces

| Surface | Emits Receipt? | Schema? | Storage | Chain of Custody? | Evidence | Gap |
|---|---|---|---|---|---|---|
| `pm_update_work_item` → Leantime | yes | `CanonicalReceipt {canonical_system="leantime", canonical_id, success, operation_type="metadata_update", version, mirror_receipts=[], reconciliation_state="SYNCED"}` | response only (caller-owned) | no persistent receipt | [src/dopemux/pm/writes.py:234–240](src/dopemux/pm/writes.py#L234) | no chronicle of metadata updates |
| `pm_transition_work_item` → task-orchestrator | yes | `CanonicalReceipt {canonical_system="task-orchestrator", canonical_id, success, operation_type="workflow_transition", version=expected_version+1, mirror_receipts=[Leantime mirror], reconciliation_state}` | response only; task-orch internal records (opaque to caller) | partial — Leantime status mirror is a receipt, but task-orch internal store shape UNKNOWN | [src/dopemux/pm/writes.py:243–284](src/dopemux/pm/writes.py#L243) | task-orch-side persistence is bridge-mediated custom-data; no formal transition log |
| `pm_log_progress` → ConPort + dope-memory | yes | `CanonicalReceipt {canonical_system="conport", operation_type="progress_log", mirror_receipts=[{system="dope-memory", entry_id, success, error}], reconciliation_state="SYNCED"\|"PARTIAL"}` | ConPort PG/AGE + dope-memory append | yes — ConPort primary + dope-memory mirror | [src/dopemux/pm/writes.py:287–325](src/dopemux/pm/writes.py#L287); [src/dopemux/pm/chronicle_models.py:27–34](src/dopemux/pm/chronicle_models.py#L27) | mirror-failure handling silently OK (writes.py:324) |
| `pm_log_decision` → ConPort + dope-memory | yes | `CanonicalReceipt {operation_type="decision_log", …}` — wraps `pm_log_progress` with `is_decision=True` | same as above | yes | [src/dopemux/pm/writes.py:350–364](src/dopemux/pm/writes.py#L350) | same as above |
| `dope-memory append_chronicle` | yes | `PMChronicleWriteReceipt {canonical_backend="dope-memory", canonical_id, entry_id, linked_ids, success, error}` | ChronicleStore (PG + Milvus per [src/conport/memory_server.py:79–117](src/conport/memory_server.py#L79)) | yes — indexed by importance_score, timestamp, scope_hash | [src/dopemux/pm/chronicle_models.py:27–34](src/dopemux/pm/chronicle_models.py#L27); memory_server.py:132–136 | response schema not enforced by Pydantic model on caller side |
| ConPort `log_decision` / `log_progress` (direct MCP) | yes | string response from `@mcp.tool()` functions | ConPort DB | yes (per-decision row) | [docker/mcp-servers/conport/server.py:66,151](docker/mcp-servers/conport/server.py#L66) | response is unstructured string per @mcp.tool signature `-> str` |
| dopecon-bridge `/kg/decisions` POST | yes | normalized list response `_normalize_decision_list` (routes.py:152): `{count, items, decisions, query, source: "conport"}` | proxied; no bridge-side persistence | proxy only | [services/dopecon-bridge/dopecon_bridge/routes.py:152–173](services/dopecon-bridge/dopecon_bridge/routes.py#L152) | none for bridge layer |
| **Proof bundle (governance)** | should — per AGENTS.md §9 | **two competing templates**: (a) comprehensive [docs/03-reference/fast-dev-os/templates-proof/proof-bundle-template.json](docs/03-reference/fast-dev-os/templates-proof/proof-bundle-template.json) (full §9 mandate); (b) minimal [docs/03-reference/governance/codex-proof-template.json](docs/03-reference/governance/codex-proof-template.json) (skeleton, fields null) | `proof/<TP-id>/PROOF.json`, `proof_bundle/RUN_MANIFEST.json`, RTE-specific paths under `extraction/repo-truth-extractor/v*/proofs/` | **per-TP only** — no canonical receipt store; no schema validation on save | template files + 8+ sampled PROOF.json bundles | enforcement is informal: no save-time schema check; two templates coexist without reconciliation; RTE prescan receipts follow a third schema |
| **Task Packet** | yes | [docs/03-reference/spec/dopetask/dopetask-canonical-spec.json](docs/03-reference/spec/dopetask/dopetask-canonical-spec.json) (272 lines; required root fields: `id, project, target, repo_binding, series, commit, pr, steps`) | `task-packets/generated/<TP-id>.json` and `proof/<TP-id>/`-adjacent | yes when validated | AGENTS.md §5; multiple PROOF.json examples invoking `python -m jsonschema -i <tp> <schema>` | validation is operator-invoked; no save-time enforcement; no version field |
| **EventCoordinator emission** | yes (log/Redis) | event types in [event_coordinator.py:161–177](services/task-orchestrator/event_coordinator.py#L161) | Redis DB 3 (lpush/ltrim, 7-day TTL) | partial — events logged but downstream consumption is incomplete per [DOPETASK_INTEGRATION_ANALYSIS.md](DOPETASK_INTEGRATION_ANALYSIS.md) | event_coordinator.py:612–619 | no end-to-end correlation ID across event→ConPort→proof bundle |
| **PreCommit/preflight** | yes (CI artifact) | `.githooks/pre-commit` output | log files + check-run | yes via PR check | [.githooks/pre-commit](.githooks/pre-commit) | none — well-formed |
| **PAL `precommit` / `codereview` output** | yes (tool response) | JSON per pal-mcp tool schema (e.g., `verdict, issues_by_severity, continuation_id`) | tool response + PROOF bundle `codereview_status` block | yes when packed into PROOF.json | proof-bundle-template.json `codereview_status` object; PAL_HELP via .claude/MCP_PAL.md | no required ingest into proof bundle; can be omitted |

---

## 6. Safe Reuse Recommendations

> Labels: **OBSERVED** / **INFERRED** / **PROPOSED** / **UNKNOWN** / **RISK** / **REQUIRES_REPO_INSPECTION**

### Default policy (PROPOSED, awaits operator review)
- **T0/T1 auto-invoke**: safe for task-orchestrator to call without operator gate
- **T2** (draft artifact in `claudedocs/`, `out/`): safe to auto-invoke with logged receipt; user can audit
- **T3** (docs edits): require PR-style flow — write into a branch + open PR, do not commit directly
- **T4** (source/config/runtime state): explicit operator approval per invocation, default-deny
- **T5** (GitHub mutation): operator approval per invocation + human-visible diff/preview
- **T6** (destructive): refuse without typed confirmation phrase; default-deny even with operator present
- **TX / TU**: refuse, surface to human

### Per-family recommendations

**`orchestrator.status.*`** — **OBSERVED safe path exists** via `TaskOrchestratorAdapter.get_queue/get_blockers/get_state`. **PROPOSED**: wrap as 3 MCP tools (T0). Risk: adapter timeout (10s) at SessionStart latency.

**`orchestrator.plan.*`** — **PARTIAL** runtime support. **PROPOSED**: expose `task_decomposition_endpoint.py` behind an MCP tool requiring T4 approval per packet. **RISK**: implicit auto-decomposition (event_coordinator.py:437–446 on SPRINT_STARTED) is currently T5 with no approval — operator-facing tool should NOT mirror that auto-trigger behavior.

**`orchestrator.packet.*`** — **HIGH GAP**. **PROPOSED**: introduce a packet-validation MCP tool (T1, runs `jsonschema -i <tp> <spec>`) as a safe first step. Packet *ingestion* / *execution* must remain operator-driven via `scripts/dopetask` (per AGENTS.md §6 — dopetask is the execution runtime). **REQUIRES_REPO_INSPECTION**: does task-orchestrator have any packet-execution path beyond event emission? Audit window didn't surface one.

**`orchestrator.review.*`** — **PROPOSED**: wrap PAL `codereview` (T1) + `precommit` (T1) as MCP tools that emit results into ConPort decisions (T4). Approval gate on the ConPort write, not the analysis.

**`orchestrator.route.*`** — **OBSERVED** in dopecon-bridge. **PROPOSED**: do NOT add a task-orchestrator route tool — that would worsen the dopecon-bridge "Known Danger" pattern ([AGENTS.md §10](AGENTS.md)). Routing should stay in bridge; task-orchestrator should call canonical writers directly.

**`orchestrator.memory.*`** — **PROPOSED**: do NOT expose memory writes through task-orchestrator. Use canonical ConPort + dope-memory MCPs directly; task-orchestrator owns transitions only.

**`orchestrator.proof.*`** — **PROPOSED**: introduce three tools:
1. `proof.validate(tp_path)` — T1 schema check
2. `proof.assemble(tp_id)` — T2 produces draft PROOF.json
3. `proof.commit(tp_id)` — T4 saves to canonical path with operator approval
   This requires resolving the two-templates drift first.

**`orchestrator.github.*`** — **PROPOSED**: keep behind operator approval (T5). Reuse existing `dopemux-pr-merge` and `dopemux-github` CLIs rather than adding new MCP wrappers, to avoid duplicating mutation surfaces.

**`orchestrator.daily.*`** — **PROPOSED**: SessionStart enrichment is safe (T0 reads of queue/blockers/active_context); fold into existing `session_lifecycle.py` rather than create a new slash command. Time-budget per [native_hooks.py:211–216](src/dopemux/claude/native_hooks.py#L211) iteration/time guards.

### Hardening recommendations (REQUIRES_REPO_INSPECTION)
- **Dangerous-mode partial enforcement** (verified): [src/dopemux/cli.py#L3771-L3779 + L5752-L5757](src/dopemux/cli.py#L3771) SETS all 5 env vars (`DOPEMUX_DANGEROUS_MODE`, `HOOKS_ENABLE_ADAPTIVE_SECURITY`, `CLAUDE_CODE_SKIP_PERMISSIONS`, `METAMCP_ROLE_ENFORCEMENT`, `METAMCP_APPROVAL_REQUIRED`). The launcher at [src/dopemux/claude/launcher.py#L181-L189](src/dopemux/claude/launcher.py#L181-L189) consumes 2 of them (`DOPEMUX_DANGEROUS_MODE` and `CLAUDE_CODE_SKIP_PERMISSIONS`) to append `--dangerously-skip-permissions` to the Claude Code argv; `launcher.py#L373` additionally propagates `CLAUDE_CODE_SKIP_PERMISSIONS` into child env via `env.setdefault`. The remaining **3 vars (`HOOKS_ENABLE_ADAPTIVE_SECURITY`, `METAMCP_ROLE_ENFORCEMENT`, `METAMCP_APPROVAL_REQUIRED`) have no in-repo consumer** — `native_hooks.py` does not read them, and recursive grep over `src/`, `services/`, `scripts/` (excluding the cli.py setters and the launcher.py consumer for the 2 it does read) returns no production hits for these 3. Presumed consumer for the 3 is an external MetaMCP layer (UNKNOWN in this repo). **Inverse-failure risk applies specifically to those 3 vars**: an operator invoking `/dangerous` correctly gets `--dangerously-skip-permissions` on Claude Code, but if MetaMCP isn't loaded or not configured to consume the role/approval/adaptive-security vars, those guards remain in their default state while the operator believes they are toggled off. Task-orchestrator must not assume MetaMCP-tier gates are disabled just because env vars are present.
- **DPMX_LIVE_OK consent gate**: [src/dopemux/cli.py:4906–4916](src/dopemux/cli.py#L4906) — duplicated check (cli.py + `run_repscan.py`); defense in depth. Pattern is reusable for any orchestrator T5+ operation.
- **`/api/coordination/events` emit-without-consume** ([DOPETASK_INTEGRATION_ANALYSIS.md](DOPETASK_INTEGRATION_ANALYSIS.md)): until ConPort subscription is wired, any task-orchestrator-emitted event is effectively a write-to-nowhere from a chain-of-custody perspective.

---

## 7. Blocked / Refuse List

Surfaces task-orchestrator **must NOT expose as automatic MCP tools** without explicit human approval per invocation, plus rationale.

| Surface | Why Blocked |
|---|---|
| `dope-context.clear_index` | **T6 destructive**. Wipes all Qdrant collections for the workspace with no recovery. No quarantine, no soft-delete. Even per-call confirmation is insufficient — should require typed phrase + operator presence. |
| ConPort `delete_*` family (`delete_decision_by_id`, `delete_progress_by_id`, `delete_custom_data`, `delete_system_pattern_by_id`) | **T5 irreversible**. Decisions and progress are the authority for project history; deletion mutates the knowledge graph permanently. Block from auto-invoke; require operator action. |
| ConPort `promote_all` | **T5 unbounded batch**. Promotes all instance-local progress to shared without per-item review. Block from auto-invoke; require explicit list or confirmation. |
| ConPort `fork_instance` | **T4–T5 cross-workspace propagation**. No source/target validation visible; can cross workspace boundaries. Block from auto-invoke. |
| `Desktop Commander.focus_window` / `.type_text` | **T4 alien-process state mutation**. Can affect any open application window outside the repo (modify open documents, hijack input). Block; operators should drive desktop control directly. |
| `dopecon-bridge /route/pm` for `WORKFLOW_SIGNIFICANT_OPERATIONS` | **T5 routed mutation with advisory-only guard**. Bridge's `_is_workflow_significant_pm_mutation` (routes.py:145–151) classifies but does not hard-block. Task-orchestrator must not wrap this — go through canonical writers in `src/dopemux/pm/writes.py` instead. |
| `EventCoordinator auto-update of .claude/CLAUDE.md` ([event_coordinator.py:444](services/task-orchestrator/event_coordinator.py#L444)) | **T4 silent doc rewrite** on SPRINT_STARTED. Mutates a committed governance file. Should not be exposed as a tool at all; existing automation should be gated by operator opt-in. |
| `.github/workflows/gemini-scheduled-triage.yml` downstream consumer | Job itself is T0 (permissions: issues:read, pull-requests:read), but its `triaged_issues` output may be consumed by a follow-on workflow with write permissions. **REQUIRES_REPO_INSPECTION** of any downstream workflow before exposing as a tool. |
| `task-orchestrator /api/coordination/events` (emit) **with no consumer wired** | **DOPETASK_INTEGRATION_ANALYSIS.md** confirms emitter-only state. Emitting events when no consumer exists creates the illusion of audit chain while data is lost. Block "emit on operator action" until consumer is implemented. |
| External v3 task-orchestrator `complete_tree` / `manage_dependencies` / `manage_items` / `advance_item` | **TX**. Source is not in this repo; tool behavior, schema, and guard-rails not verifiable. Block from auto-invoke until source is identified and tools are tiered. |
| Leantime Bridge MCP tools | **TU**. Tool list not enumerated in audit window. Block from auto-invoke. |
| `_on_stop` safe-stop bypass | **T4 runtime gate**. `native_hooks.py:282–313` blocks Stop on missing completion-token. Do NOT add a tool that pre-emptively writes a completion-token; that would bypass the gate. |

---

## 8. Evidence Ledger

### Direct commands (exit codes captured where surfaced)

| # | Command | Exit | Output Summary |
|---|---|---|---|
| 1 | `find . -maxdepth 4 -name "mcp-proxy-config*"` | 0 | Three configs: `mcp-proxy-config.yaml`, `mcp-proxy-config.json`, `mcp-proxy-config.copilot.yaml` |
| 2 | `ls .claude/hooks/` | 0 | 6 scripts: check_energy.sh, log_progress.sh, prompt_analyzer.py, save_context.sh, session_lifecycle.py, track_file_edit.sh |
| 3 | `cat .claude/settings.json \| head -120` | 0 | All 10 lifecycle events route through `src/dopemux/claude/native_hooks.py` (single dispatcher pattern) |
| 4 | `ls src/conport/` | 0 | Only `memory_server.py` (unified-memory variant; Milvus+PostgreSQL backend) |
| 5 | `ls docker/mcp-servers/` and `ls docker/mcp-servers-source/` | 0 | Identical 26-entry listings (likely symlinked or duplicated) |
| 6 | `find -type d \| grep -E "(plugin\|hook\|workflow\|coordination\|event\|receipt\|approval\|gate\|safety\|proof)"` | 0 | Identified: `.claude/hooks`, `.claude/modules/coordination`, `.claude/workflows`, `.githooks`, `.github/workflows`, `plugins/Dopemux/` (Leantime), `docker/leantime/plugins/`, `docs/03-reference/fast-dev-os/templates-proof/`, `out/proofs/`, `out/proof/`, `extraction/repo-truth-extractor/*/proofs/`, `SYSTEM_ARCHIVE/.../shared/safety` (archived) |
| 7 | `find services/task-orchestrator -name "*.py" \| xargs grep -l "manage_items\|advance_item\|complete_tree"` | 1 (no matches) | **VERIFIED**: v3 task-orchestrator MCP tools (manage_items, advance_item, complete_tree, etc.) are **NOT in this repo**. They belong to an external `task-orchestrator` MCP server loaded via mcp-proxy-config. |
| 8 | `grep -n "def \|@mcp\|@app\|tool(" docker/mcp-servers/conport/server.py` | 0 | 13 `@mcp.tool()` decorators at lines 35, 46, 54, 65, 81, 90, 99, 108, 119, 126, 133, 142, 150 — verified tool list |
| 9 | `head -40 src/conport/memory_server.py` | 0 | Header docstring confirms unified-memory variant: `mem.upsert/search` + `graph.link/neighbors` over Milvus + PostgreSQL + Zep. Imports `mcp.server.stdio.stdio_server`. |
| 10 | `grep -rn "DOPEMUX_DANGEROUS_MODE\|HOOKS_ENABLE_ADAPTIVE_SECURITY\|CLAUDE_CODE_SKIP_PERMISSIONS\|METAMCP_ROLE_ENFORCEMENT\|METAMCP_APPROVAL_REQUIRED" src/ services/ scripts/` | 0 | Setters live in [src/dopemux/cli.py](src/dopemux/cli.py) lines 3732, 3771-3779, 3794-3800, 3814, 5752-5757, 5766-5769. **In-repo consumers found**: [src/dopemux/claude/launcher.py#L181-L189](src/dopemux/claude/launcher.py#L181-L189) reads `os.environ.get("CLAUDE_CODE_SKIP_PERMISSIONS")` and `os.environ.get("DOPEMUX_DANGEROUS_MODE")` to append `--dangerously-skip-permissions` to the Claude Code argv; launcher.py#L373 force-sets `CLAUDE_CODE_SKIP_PERMISSIONS=true` into the child env (`env.setdefault` in `_prepare_environment`). **VERIFIED partial split**: 2 of 5 vars (CLAUDE_CODE_SKIP_PERMISSIONS, DOPEMUX_DANGEROUS_MODE) ARE consumed at the launcher layer; the other 3 (HOOKS_ENABLE_ADAPTIVE_SECURITY, METAMCP_ROLE_ENFORCEMENT, METAMCP_APPROVAL_REQUIRED) have no in-repo consumer and presumably enforce at an external MetaMCP layer. **Partial enforcement, scoped to the 3 MetaMCP-tier vars.** |
| 11 | `cat .github/workflows/gemini-scheduled-triage.yml \| head -80` | 0 | **VERIFIED** workflow permissions: `permissions: {contents: read, id-token: write, issues: read, pull-requests: read}` (line ~38). Job is read-only at GitHub permissions layer. Downstream consumer of `triaged_issues` output unverified. |

### Agent reports synthesized (3 parallel Explore agents)

1. **MCP tool catalog with mutation tiers** — full per-server enumeration with file:line citations; consolidated tier-sorted table; flagged tools without approval guards; identified `clear_index` as T6 and `promote_all`/`fork_instance`/`delete_*` as T5.
2. **Hooks / events / workflow / coordination deep-dive** — per-hook behavior (check_energy.sh, log_progress.sh, save_context.sh, track_file_edit.sh, prompt_analyzer.py, session_lifecycle.py), native_hooks.py dispatcher with EXIT_BLOCK behavior, EventCoordinator (13 event types, 9 workers), ImplicitAutomationEngine (4 workflows), dopecon-bridge route inventory, CI/CD automation including gemini-scheduled-triage.
3. **Receipt / proof / approval / guard audit** — two competing proof templates (comprehensive vs minimal), Task Packet schema details, per-canonical-writer receipt shapes (CanonicalReceipt, PMChronicleWriteReceipt), approval gates inventory (DPMX_LIVE_OK, safe-tool allowlist, iteration/time limits, phase transition, repo preflight), dangerous-mode env vars documented but not enforced in hook layer, cited gaps between AGENTS.md mandates and code.

### Key files inspected
- [AGENTS.md](AGENTS.md) — §§6, 7, 9 referenced extensively
- [PM_PLANE.md](PM_PLANE.md) — §5 (write paths)
- [.claude/settings.json](.claude/settings.json) — hooks block
- [.claude/hooks/](.claude/hooks/) — all 6 scripts
- [src/dopemux/claude/native_hooks.py](src/dopemux/claude/native_hooks.py) — dispatcher + 10 handlers
- [src/dopemux/pm/writes.py](src/dopemux/pm/writes.py) — canonical writers + CanonicalReceipt
- [src/dopemux/pm/chronicle_models.py](src/dopemux/pm/chronicle_models.py) — PMChronicleWriteReceipt
- [src/dopemux/pm/adapters/orchestrator.py](src/dopemux/pm/adapters/orchestrator.py) — TaskOrchestratorAdapter
- [src/dopemux/cli.py](src/dopemux/cli.py) — dangerous-mode env-var setters; DPMX_LIVE_OK consent
- [src/conport/memory_server.py](src/conport/memory_server.py) — unified-memory variant
- [services/task-orchestrator/app/main.py](services/task-orchestrator/app/main.py) — FastAPI + FastMCP wiring
- [services/task-orchestrator/task_orchestrator/mcp/__init__.py](services/task-orchestrator/task_orchestrator/mcp/__init__.py) — 6 stdio MCP tools
- [services/task-orchestrator/event_coordinator.py](services/task-orchestrator/event_coordinator.py) — 13 event types, 9 workers
- [services/task-orchestrator/automation_workflows.py](services/task-orchestrator/automation_workflows.py) — 4 implicit workflows
- [services/dopecon-bridge/dopecon_bridge/routes.py](services/dopecon-bridge/dopecon_bridge/routes.py) — 7+ route prefixes, WORKFLOW_SIGNIFICANT_OPERATIONS check
- [docker/mcp-servers/conport/server.py](docker/mcp-servers/conport/server.py) — 13 MCP tools
- [docker/mcp-servers/exa/exa_server.py](docker/mcp-servers/exa/exa_server.py) — 4 tools
- [docker/mcp-servers/desktop-commander/server.py](docker/mcp-servers/desktop-commander/server.py) — 4 tools
- [services/dope-context/src/mcp/server.py](services/dope-context/src/mcp/server.py) — 18 tools incl. `clear_index` T6
- [docs/03-reference/spec/dopetask/dopetask-canonical-spec.json](docs/03-reference/spec/dopetask/dopetask-canonical-spec.json) — 272-line schema
- [docs/03-reference/fast-dev-os/templates-proof/proof-bundle-template.json](docs/03-reference/fast-dev-os/templates-proof/proof-bundle-template.json) — comprehensive proof schema
- [docs/03-reference/governance/codex-proof-template.json](docs/03-reference/governance/codex-proof-template.json) — minimal proof skeleton
- [.claude/commands/dangerous.md](.claude/commands/dangerous.md) — documented env vars
- [.claude/commands/safe.md](.claude/commands/safe.md) — revert mode
- [.githooks/pre-commit](.githooks/pre-commit) — preflight enforce
- [.github/workflows/preflight.yml](.github/workflows/preflight.yml), [codeql.yml](.github/workflows/codeql.yml), [gemini-scheduled-triage.yml](.github/workflows/gemini-scheduled-triage.yml)
- [mcp-proxy-config.yaml](mcp-proxy-config.yaml), [mcp-proxy-config.json](mcp-proxy-config.json), [mcp-proxy-config.copilot.yaml](mcp-proxy-config.copilot.yaml)

### Confidence and unknowns

- Confidence: **HIGH** for in-repo MCP tool counts, hook handler behavior, EXIT_BLOCK gate locations, dangerous-mode env-var SET vs CONSUMED split, gemini-scheduled-triage permissions block.
- Confidence: **MEDIUM** for proof template enforcement (templates exist; whether all proof bundles validate against them at save-time was not testable in read-only mode).
- Confidence: **MEDIUM** for EventCoordinator downstream effects (handler signatures present; full mutation chain not traced past 1 hop in some cases — TASK_COMPLETED, SPRINT_ENDED, SYNC_REQUIRED, CONFLICT_DETECTED handlers only have signatures in excerpt).
- **UNKNOWN**: external v3 task-orchestrator source location; full Leantime Bridge MCP tool list; downstream consumer of `gemini-scheduled-triage.yml` `triaged_issues` output; MetaMCP layer behavior (where dangerous-mode env vars are presumably consumed).
- **REQUIRES_REPO_INSPECTION**: how is `mcp-proxy-config.yaml` consumed at session-start? What MetaMCP build is loaded? These are the gate-enforcement consumers of the dangerous-mode env vars.

### Final repo-truth verdict

The repo has substantial existing infrastructure for the safety primitives a task-orchestrator integration needs (canonical writers, receipts, proof templates, lifecycle hooks, EXIT_BLOCK guards), but several critical gaps will block a safe operator-facing surface:

1. **Two task-orchestrator MCP surfaces coexist** (local 6-tool + external v3 13-tool) with no source visible for the latter in this repo. Tier classification is impossible for the external surface without reading its source.
2. **Dangerous mode is partially enforced (2 of 5 vars)**: env vars are SET by [cli.py#L3771-L3779](src/dopemux/cli.py#L3771); [launcher.py#L181-L189](src/dopemux/claude/launcher.py#L181-L189) consumes `CLAUDE_CODE_SKIP_PERMISSIONS` and `DOPEMUX_DANGEROUS_MODE` to append `--dangerously-skip-permissions` to the Claude Code argv. The remaining 3 vars (`HOOKS_ENABLE_ADAPTIVE_SECURITY`, `METAMCP_ROLE_ENFORCEMENT`, `METAMCP_APPROVAL_REQUIRED`) have **no in-repo consumer**; their enforcement (if any) presumably lives in an external MetaMCP layer. Task-orchestrator must not assume MetaMCP-tier gates are disabled just because the env vars are present. **Inverse-failure risk** applies to those 3 vars: operator may believe role enforcement and approval gates are disabled when in fact MetaMCP-tier behavior is unchanged.
3. **Implicit automation triggers T4–T5 mutations without operator approval**: SPRINT_STARTED auto-decomposition ([event_coordinator.py:437–446](services/task-orchestrator/event_coordinator.py#L437)), `.claude/CLAUDE.md` auto-rewrite ([event_coordinator.py:444](services/task-orchestrator/event_coordinator.py#L444)), context auto-save on CONTEXT_SWITCH heuristic ([automation_workflows.py:196–217](services/task-orchestrator/automation_workflows.py#L196)). Any new operator-facing surface must not mirror these auto-trigger patterns.
4. **`dope-context.clear_index` is a T6 destructive tool with no guard** ([dope-context/src/mcp/server.py:1586](services/dope-context/src/mcp/server.py#L1586)). Should be on a per-call typed-confirmation gate, not merely operator approval.
5. **ConPort writes have zero approval guards**; `promote_all` and `fork_instance` are particularly hazardous.
6. **Proof regime is dual-template + RTE-third-template**, with no save-time schema validation. Resolving this is a prerequisite to building `orchestrator.proof.*` tools.
