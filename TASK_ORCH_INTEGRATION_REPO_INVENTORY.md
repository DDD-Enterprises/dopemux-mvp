# TASK_ORCH_INTEGRATION_REPO_INVENTORY

Runtime-evidence inventory for integrating `task-orchestrator` into Dopemux daily operator workflows.

Every claim cites runtime/source evidence. Doctrine docs are quoted but never outrank runtime per [AGENTS.md §2](AGENTS.md). `UNKNOWN` and `CONFLICTING` are preserved, not laundered.

Generated: 2026-05-25. HEAD: `7037c5f29df11ca3fec55f991a4805e86e997e1e`.

---

## 1. Repo Identity

| Field | Value | Evidence |
|---|---|---|
| Repo root (worktree) | `/Users/hue/code/dopemux-mvp/.claude/worktrees/beautiful-pascal-d3361e` | `pwd` + `git rev-parse --show-toplevel` |
| Primary checkout | `/Users/hue/code/dopemux-mvp` (parent) | git worktree convention |
| Branch | `claude/beautiful-pascal-d3361e` | `git branch --show-current` |
| HEAD commit | `7037c5f29df11ca3fec55f991a4805e86e997e1e` | `git rev-parse HEAD` |
| Dirty state | clean | `git status --short` (empty) |
| Remotes | `origin` + `mvp` → `https://github.com/DDD-Enterprises/dopemux-mvp.git` | `git remote -v` |
| Recent commit subject | `fix(pr-merge): allow GEMINI_CLI_TRUST_WORKSPACE in isolated env and add --skip-trust` | git log |

---

## 2. Observed Runtime Entrypoints

| System | Entrypoint | Evidence Path | Runtime Status | Notes |
|---|---|---|---|---|
| **dopemux CLI** | `dopemux.cli:main` | [pyproject.toml:136–141](pyproject.toml) `[project.scripts]` | active | also `dopemux-mobile`, `dopemux-github`, `dopemux-pr-merge` |
| **task-orchestrator (canonical)** | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | [services/task-orchestrator/Dockerfile:43](services/task-orchestrator/Dockerfile#L43) → [services/task-orchestrator/app/main.py](services/task-orchestrator/app/main.py) | active in compose | FastAPI + FastMCP; port 8000 |
| **task-orchestrator (legacy, hard-fail)** | [services/task-orchestrator/task_orchestrator/app.py](services/task-orchestrator/task_orchestrator/app.py) | `sys.exit(1)` immediately at module import | **explicit stub** | Guard text: "UNSUPPORTED RUNTIME … route to canonical runtime in app/main.py" |
| **task-orchestrator (stdio MCP fallback)** | `mcp_stdio.py` → `mcp.run(transport="stdio")` | [services/task-orchestrator/mcp_stdio.py](services/task-orchestrator/mcp_stdio.py) | present, not in Dockerfile CMD | only invoked if a parent calls it directly |
| **dopecon-bridge** | `app = FastAPI(...)` line 54 | [services/dopecon-bridge/main.py](services/dopecon-bridge/main.py) | active in compose (port 3016) | router/proxy only per AGENTS.md §6 |
| **dope-context** | services/dope-context (no top-level main.py; MCP-based) | [compose.yml dope-context block](compose.yml) | active in compose (port 3010) | search_code / search_all / index_workspace |
| **adhd-engine (real)** | `services/adhd_engine/main.py` | underscore variant, populated | active in compose (3025 host → 8095 container) | NOT `services/adhd-engine/` (that's a 1-file stub) |
| **adhd-engine (stub)** | `services/adhd-engine/auth.py` | 1 file, 1.25 KB total | **stub** | dash-spelling variant; not wired |
| **working-memory-assistant** | `main.py` (port 8096 internally; built as `dope-memory` image) | [compose.yml `dope-memory` service](compose.yml) builds from `services/working-memory-assistant/Dockerfile.dope-memory` | active in compose (port 3020) | image labeled `dope-memory` but source path is `working-memory-assistant` (DRIFT) |
| **serena** | docker MCP image (`docker/mcp-servers/serena/Dockerfile`) | [compose.yml serena block](compose.yml) | active in compose (3006 + 4006) | also has `services/serena/` host-side scripts |
| **conport** | `docker/mcp-servers/conport/Dockerfile` | [compose.yml conport block](compose.yml) | active in compose (3004 HTTP + 3005 MCP/SSE) | dual-interface (HTTP and MCP) |
| **pal** | `docker/mcp-servers/pal/Dockerfile` | [compose.yml pal block](compose.yml) | active in compose (3003) | renamed from `zen-mcp` |
| **dopetask runtime** | `scripts/dopetask` → installs `dopetask==0.5.1` into `.dopetask_venv/` and `exec`s | [scripts/dopetask:97](scripts/dopetask) | active | requires `.dopetaskroot` + `.dopetask-pin` in repo root |
| **taskx shim** | `scripts/taskx` (6-line bash) | [scripts/taskx](scripts/taskx) | active, deprecating | delegates to `scripts/dopetask` per AGENTS.md §6 |
| **mcp-integration-bridge** | `services/mcp-integration-bridge/main.py` | hardcodes `http://{prefix}-task-orchestrator:3014` line 58 | **not in compose.yml** | dead-end client; expects port 3014 that no longer exists |
| **repo-truth-extractor** | library/CLI; no HTTP main.py | `services/repo-truth-extractor/` | runtime UNKNOWN as HTTP service | feeds dope-context |

---

## 3. Observed System Roles

| System | OBSERVED Role | Must Not Own | Evidence | UNKNOWN / CONFLICTING |
|---|---|---|---|---|
| **dopemux** | operator CLI, startup, routing, MCP/service coordination | PM, decisions, code retrieval | [AGENTS.md §6](AGENTS.md) line 75; [PM_PLANE.md §3.dopemux](PM_PLANE.md) "PM-plane coordinator and normalization layer, not the PM system of record" | none |
| **task-orchestrator** | workflow transitions; workflow queue/blockers/state read APIs; bridge-mediated workflow record persistence | passive PM metadata; structured decisions; chronicle; agent runtime authority | [AGENTS.md §6 line 80](AGENTS.md); [PM_PLANE.md §3.task-orchestrator](PM_PLANE.md); writes via `pm_transition_work_item` in [src/dopemux/pm/writes.py](src/dopemux/pm/writes.py) | AGENTS.md §10 flags "runtime authority is conflicted across app/main.py, task_orchestrator/app.py, and Docker wiring" — RESOLVED in code (task_orchestrator/app.py hard-fails); doctrine docs stale |
| **dopetask** | external execution runtime; pinned 0.5.1 | PM metadata; workflow legality; decisions | [AGENTS.md §6 line 79](AGENTS.md); [.dopetask-pin](.dopetask-pin); [scripts/dopetask:97](scripts/dopetask) | known: doctor subcommand fails on non-main branches (script lines 86–95) |
| **ConPort** | structured decisions, progress, project context; semantic retrieval | passive PM metadata; canonical workflow transitions; chronicle history | [AGENTS.md §6 line 81](AGENTS.md); [PM_PLANE.md §3.ConPort](PM_PLANE.md); writes via `conport_client.record_progress` in [src/dopemux/pm/writes.py](src/dopemux/pm/writes.py) | dual interface 3004 (HTTP) + 3005 (MCP/SSE) — context reads use 3005, decision reads use 3004 ([PM_PLANE.md §4.1](PM_PLANE.md): *"observed drift, not a single clean read contract"*) |
| **Serena** | code-intelligence MCP support; LSP + semantic; ADHD accommodations | PM truth | [compose.yml serena](compose.yml); [.claude/CLAUDE.md cognitive plane](.claude/CLAUDE.md) | duplicated across `docker/mcp-servers/serena/` and `services/serena/` |
| **dope-memory** | durable historical receipts / chronicle sink (mirror of PM activity) | PM metadata; workflow legality; queue state; structured decision authority | [PM_PLANE.md §3.dope-memory](PM_PLANE.md); [AGENTS.md §6 line 82](AGENTS.md); writes via `memory_client.append_chronicle` in [src/dopemux/pm/writes.py](src/dopemux/pm/writes.py) | compose service named `dope-memory` but image builds from `services/working-memory-assistant/Dockerfile.dope-memory` (DRIFT) |
| **dope-context** | deterministic code/docs indexing and retrieval (MCP) | PM truth; persistent decisions | [AGENTS.md §6 line 83](AGENTS.md); [compose.yml dope-context](compose.yml); Qdrant on 6333 | UNKNOWN: autonomous indexing controllers — referenced in tools list but daemon entrypoint not visible |
| **dopecon-bridge** | bridge/proxy/event transport ONLY (per [AGENTS.md §6](AGENTS.md) + §10 "Known Dangers") | **anything canonical** (task, workflow, decision, progress, PM, chronicle, retrieval) | [AGENTS.md §6 line 84](AGENTS.md); [AGENTS.md §10 first bullet](AGENTS.md); [PM_PLANE.md §3.dopecon-bridge](PM_PLANE.md) | DANGER per AGENTS.md §10: *"exposes broad surfaces that can look authoritative"* — workflow records actually persist through bridge custom-data categories ([PM_PLANE.md §3.task-orchestrator](PM_PLANE.md)) |
| **ADHD Engine** | operator state, cognitive-state, recommendations, hooks; calls ConPort for decisions | PM writes; workflow transitions | [AGENTS.md §6 line 85](AGENTS.md); [services/adhd_engine/main.py](services/adhd_engine/main.py) | underscore (`adhd_engine`) is real; dash (`adhd-engine`) is 1-file stub — confused naming |
| **Repo Truth Extractor** | extraction/audit runtime; outputs are evidence artifacts | runtime authority of any kind | [AGENTS.md §6 line 86](AGENTS.md) + [AGENTS.md §7 RTE Safety Invariants](AGENTS.md) | UNKNOWN as HTTP service in compose |
| **Leantime** | passive PM metadata authority + sprint/project snapshot authority | workflow legality; decision context; chronicle history | [PM_PLANE.md §3.Leantime](PM_PLANE.md); writes via `leantime_client.update_task` in [src/dopemux/pm/writes.py](src/dopemux/pm/writes.py); [compose.yml leantime](compose.yml) port 8080 | none for PM scope |
| **agents** (`services/agents/`, `src/dopemux/agent_orchestrator.py`, `services/task-orchestrator/task_orchestrator/agents/`) | varied (cognitive_guardian, task_decomposer, two_plane_orchestrator, memory_agent, workflow_coordinator, persona_enhancer, tool_orchestrator) | PM truth (explicit per AGENTS.md §6) | [AGENTS.md §6 final paragraph](AGENTS.md); [AGENTS.md §10](AGENTS.md) *"Agent responsibilities are duplicated across multiple families"* | **UNKNOWN**: AGENTS.md §6 explicitly: *"agent runtime authority remains `UNKNOWN` … unless a specific runtime path is verified"* |

---

## 4. Task-Orchestrator Surface Inventory

> Line numbers spot-verified against `services/task-orchestrator/app/main.py` (read offset 300, limit 200): `/health` at line 307, `/info` at line 350, `/metrics` at line 380, `/api/workflow/ideas` POST at line 441, GET at line 455, PATCH `/api/workflow/ideas/{idea_id}` at line 469, promote endpoint at line 483. MCP tool line numbers come from subagent inventory of `task_orchestrator/mcp/__init__.py` (FastMCP wiring verified via app/main.py imports). Coordination route line numbers come from subagent inventory and have not been re-verified at this offset.

| Surface | Path | Type | Read/Write | Authority Claim | Evidence | Risk |
|---|---|---|---|---|---|---|
| `/health` | `app/main.py:307–348` | HTTP GET | Read | service health | Dockerfile healthcheck uses this | LOW |
| `/info` | `app/main.py:350–377` | HTTP GET | Read | service discovery; reports "37 tools" | line 372 self-report | MED — count claim does not match `task_orchestrator/mcp/__init__.py` (6 tools defined) |
| `/metrics` | `app/main.py:380–410` | HTTP GET | Read | Prometheus | LOW |
| `/api/workflow/ideas` | `app/main.py:441–481` | HTTP POST/GET/PATCH | Write | Workflow ideas CRUD | persisted via DopeconBridge custom-data category `workflow_ideas` ([PM_PLANE.md §5](PM_PLANE.md)) | MED — bridge-mediated persistence |
| `/api/workflow/epics` | `app/main.py:501–546` | HTTP POST/GET/PATCH | Write | Workflow epics CRUD | persisted via DopeconBridge custom-data category `workflow_epics` | MED |
| `/api/projects/{id}/workflow/queue` | `app/api/project_workflow.py` | HTTP GET | Read | priority queue | [PM_PLANE.md §4.2](PM_PLANE.md) confirms canonical | LOW |
| `/api/projects/{id}/workflow/blockers` | `app/api/project_workflow.py` | HTTP GET | Read | blockers | [PM_PLANE.md §4.2](PM_PLANE.md) | LOW |
| `/api/projects/{id}/workflow/state` | `app/api/project_workflow.py` | HTTP GET | Read | workflow state | [PM_PLANE.md §4.2](PM_PLANE.md) | LOW |
| `/api/projects/{id}/workflow/transition` | `app/api/project_workflow.py` | HTTP POST | Write | **CANONICAL workflow transition** | [PM_PLANE.md §5.2](PM_PLANE.md) | HIGH — single source of truth for transitions |
| `/api/pm/work-items/{task_id}/transition` | `app/api/pm_tools.py` | HTTP POST | Write | per-work-item transition | called by `pm_transition_work_item` in [src/dopemux/pm/writes.py](src/dopemux/pm/writes.py) | HIGH |
| `/api/coordination/operations` | `app/main.py:549–579` | HTTP POST | Write | cross-plane ops | LOW |
| `/api/coordination/health` | `app/main.py:582–603` | HTTP GET | Read | plane health | LOW |
| `/api/coordination/metrics` | `app/main.py:606–617` | HTTP GET | Read | coord metrics | LOW |
| `/api/coordination/events` | `app/main.py:620–663` | HTTP POST | Write | emit events | MED — emits to dopecon-bridge but [DOPETASK_INTEGRATION_ANALYSIS.md](DOPETASK_INTEGRATION_ANALYSIS.md) notes no consumer wired |
| `/api/coordination/conflicts` | `app/main.py:666–728` | HTTP GET/POST | Read/Write | conflict tracking | MED — resolution strategy unclear |
| `/api/coordination/status` | `app/main.py:796–818` | HTTP GET | Read | LOW |
| `/api/coordination/test` | `app/main.py:821–854` | HTTP POST | Write | test only | LOW |
| `/ws/coordination` | `app/main.py:731–789` | WebSocket | Write | real-time event broadcast | uses `ConnectionManager` lines 228–273 | MED |
| MCP tool `analyze_dependencies` | `task_orchestrator/mcp/__init__.py:22–42` | stdio MCP | Read | task dependency detection | wired to FastMCP via app/main.py:82–98 | LOW |
| MCP tool `batch_tasks` | `task_orchestrator/mcp/__init__.py:44–62` | stdio MCP | Write | ADHD task batching | LOW |
| MCP tool `get_adhd_state` | `task_orchestrator/mcp/__init__.py:64–69` | stdio MCP | Read | session state from `adhd_monitor` | LOW |
| MCP tool `get_task_recommendations` | `task_orchestrator/mcp/__init__.py:72–88` | stdio MCP | Read | energy-aware recs | LOW |
| MCP tool `record_break` | `task_orchestrator/mcp/__init__.py:91–96` | stdio MCP | Write | break tracking | LOW |
| MCP tool `get_agent_status` | `task_orchestrator/mcp/__init__.py:99–105` | stdio MCP | Read | agent pool status | LOW |
| `PlaneCoordinator` | `app/core/coordinator.py:130+` | service class | Write | two-plane coordination state machine | manages events, conflicts, sync engine | MED |
| `WorkflowService` / `workflow_store.py` | `app/services/workflow_store.py` | service class | Write | stores ideas/epics/audit via `AsyncDopeconBridgeClient.save_custom_data` | [PM_PLANE.md §5.4](PM_PLANE.md) | MED — bridge-mediated, not local DB |
| `TaskOrchestratorAdapter` (client) | [src/dopemux/pm/adapters/orchestrator.py:10–15](src/dopemux/pm/adapters/orchestrator.py#L10) | client adapter | Read/Write | reads queue/blockers/state, posts transitions | `TASK_ORCHESTRATOR_URL` default = `http://localhost:8000` (line 15; explicit comment "Active runtime authority is app.main on port 8000 in this checkout") | LOW — repo truth aligned |

**Hard-fail stub (not a surface, but listed for completeness)**:
- [services/task-orchestrator/task_orchestrator/app.py](services/task-orchestrator/task_orchestrator/app.py) calls `sys.exit(1)` immediately. Guard text: *"UNSUPPORTED RUNTIME … This Task Orchestrator runtime variant is no longer supported for PM-plane use. All traffic must be routed to the canonical runtime in app/main.py (Port 8000)."* This **resolves** the conflict AGENTS.md §10 still flags as open.

---

## 5. PM / Memory / Retrieval Boundary Map

Canonical writers per concern, with reader/consumer paths and storage backends. Source of truth: [src/dopemux/pm/writes.py](src/dopemux/pm/writes.py), [src/dopemux/pm/reads.py](src/dopemux/pm/reads.py), [PM_PLANE.md](PM_PLANE.md), [AGENTS.md §6](AGENTS.md).

| Concern | Canonical Writer | Reader / Consumer | Storage | Evidence | Risk |
|---|---|---|---|---|---|
| **PM metadata** (title, assignee, description, dates, labels) | Leantime via `leantime_client.update_task(...)` in `pm_update_work_item` | `LeantimeJSONRPCClient.get_project/get_tickets` for snapshots | Leantime MySQL (external) | [PM_PLANE.md §5.1](PM_PLANE.md) | Leantime unavailable → metadata frozen |
| **Workflow transitions** (state machine) | task-orchestrator via `pm_transition_work_item` → `orchestrator_client.transition(...)` | TaskOrchestratorAdapter reads queue/blockers/state | bridge-mediated custom-data; mirrored to Leantime status | [PM_PLANE.md §5.2](PM_PLANE.md); [AGENTS.md §6 line 80](AGENTS.md) | task-orchestrator down → transitions blocked |
| **Workflow views** (queue, blockers, state) | task-orchestrator `app/api/project_workflow.py` | dopemux PM reads, UI, CLI, agents | derived from runtime state OR bridge custom-data | [PM_PLANE.md §4.2](PM_PLANE.md) *"one authority slice with two internal read modes"* | cache-miss → derived/stored fallback |
| **Workflow ideas / epics / audit** | task-orchestrator `WorkflowService` via `AsyncDopeconBridgeClient.save_custom_data` | task-orchestrator read APIs | DopeconBridge categories: `workflow_ideas`, `workflow_epics`, `workflow_audit` | [PM_PLANE.md §5.4](PM_PLANE.md) | bridge proxy outage → workflow record persistence blocked |
| **Decisions** (ADRs, project decisions) | ConPort via `conport_client.record_progress(..., is_decision=True)` | dopemux PM reads via `ConPortAdapter.search_decisions` (CONPORT_URL=3004); UI, agents | ConPort PostgreSQL/AGE | [PM_PLANE.md §5.3](PM_PLANE.md); writes.py `pm_log_decision` line 350 | ConPort down → decisions unrecorded |
| **Progress entries** | ConPort via `conport_client.record_progress` (primary) | dopemux PM reads; mirrored to dope-memory chronicle | ConPort PostgreSQL/AGE; dope-memory mirror | [PM_PLANE.md §5.3](PM_PLANE.md); writes.py `pm_log_progress` | LOW – dual-write provides redundancy |
| **Custom data** (kv per category) | ConPort `/kg/custom_data` proxied via dopecon-bridge `/kg/*` | any service needing arbitrary metadata | ConPort | [PM_PLANE.md §5.3](PM_PLANE.md); [routes.py](services/dopecon-bridge/dopecon_bridge/routes.py) | ConPort down → custom-data writes lost |
| **Chronicle / receipts** (audit log of operator actions) | dope-memory via `memory_client.append_chronicle` (mirror after ConPort) | operators; replay tooling | dope-memory (port 3020) | [PM_PLANE.md §3.dope-memory](PM_PLANE.md); writes.py mirror block | LOW — receipt-mode tracking writes.py:333–347 |
| **Project context** | ConPort `ConPortClient.get_active_context` via `CONPORT_CONTEXT_URL` (default `http://localhost:3005`) | dopemux PM `pm_get_project_context`; labeled `canonical_backend="conport"` | ConPort | [PM_PLANE.md §4.1](PM_PLANE.md) | dual-URL drift inside ConPort integration itself |
| **Decision context** | ConPort `ConPortAdapter.search_decisions` via `CONPORT_URL` (default `http://localhost:3004`) | dopemux PM `pm_get_decision_context` | ConPort | [PM_PLANE.md §4.1](PM_PLANE.md) explicit: *"observed drift, not a single clean read contract"* | MED — readers use different ConPort ports for related concerns |
| **Sprint snapshot** | Leantime `get_project/get_tickets` | `pm_get_sprint_snapshot` | Leantime | [PM_PLANE.md §4.3](PM_PLANE.md) | none |
| **Code retrieval** (semantic search of source) | dope-context indexer | Claude Code, agents | Qdrant (6333) | [AGENTS.md §6 line 83](AGENTS.md); [compose.yml dope-context](compose.yml) | index staleness |
| **Docs retrieval** | dope-context (multi-format with structure-aware chunking) | same | Qdrant | [.claude/CLAUDE.md → MCP_DopeContext.md](.claude/CLAUDE.md) | same |
| **Technical context** | Serena (LSP + semantic) | `pm_get_technical_context` (PM-adjacent, execution-side) | Serena DB | [PM_PLANE.md §4.4 UNKNOWN](PM_PLANE.md) | execution-adjacent, not core PM authority |
| **Event transport** | dopecon-bridge + Redis Streams | task-orchestrator emits, ConPort/ADHD listen | redis-events (6379) + redis-primary (6380) | [compose.yml event services](compose.yml); [AGENTS.md §6 dopecon-bridge bullet](AGENTS.md) | [DOPETASK_INTEGRATION_ANALYSIS.md](DOPETASK_INTEGRATION_ANALYSIS.md) *"event emitter only, consumer incomplete"* |
| **Operator startup** | dopemux CLI (`dopemux.cli:main`) | terminal session | none persistent | [pyproject.toml:136](pyproject.toml) | none |
| **Execution handoff** | dopetask 0.5.1 (`scripts/dopetask` → `.dopetask_venv/bin/dopetask`) | external task runner | dopetask-managed venv | [scripts/dopetask:97](scripts/dopetask) | doctor subcmd fails on non-main per pin script lines 86–95 |

---

## 6. MCP Surface Inventory

| MCP Server | Entrypoint | Tools Observed | Transport | Read/Write | Risk | Evidence |
|---|---|---|---|---|---|---|
| **ConPort (HTTP)** | `docker/mcp-servers/conport/Dockerfile` | log_decision, log_progress, get_active_context, update_active_context, log_system_pattern, log_custom_data, link_conport_items, semantic_search_conport, batch_log_items (+more) | HTTP | Read/Write | LOW | [compose.yml conport block](compose.yml); registry `conport-http` port 3004 |
| **ConPort (MCP/SSE)** | same container, different port | (same toolset over SSE) | SSE | Read/Write | LOW | compose.yml port 3005; registry `conport-mcp` port 3005 |
| **PAL** | `docker/mcp-servers/pal/Dockerfile` | thinkdeep, planner, consensus, debug, codereview, challenge, analyze, refactor, secaudit, testgen, tracer, docgen, chat, clink, precommit, version, listmodels | HTTP wrapper (also stdio in some contexts) | Read | LOW | [compose.yml pal block](compose.yml); registry port 3003 |
| **Serena (LSP)** | `docker/mcp-servers/serena/Dockerfile` | LSP + semantic code search, complexity scoring, ADHD-aware navigation | stdio + HTTP (4006) | Read | LOW | [compose.yml serena](compose.yml); registry port 3006 |
| **dope-context** | `services/dope-context/Dockerfile` | search_code, search_all, docs_search, index_workspace, index_docs, sync_workspace, sync_docs, get_index_status, start_autonomous_indexing, get_autonomous_status | HTTP | Read/Write (index) | LOW | [compose.yml dope-context](compose.yml); registry port 3010 |
| **GPT Researcher** | `docker/mcp-servers/gptr-mcp/Dockerfile` | deep_research, quick_search, write_report, get_research_sources, get_research_context | HTTP | Read | LOW | [compose.yml gptr-mcp](compose.yml); registry port 3009; pinned `gpt-researcher==0.14.8` |
| **Exa** | `docker/mcp-servers/exa/Dockerfile` | search, find_similar, get_contents | HTTP | Read | LOW | [compose.yml exa](compose.yml); registry port 3011 |
| **Desktop Commander** | `docker/mcp-servers/desktop-commander/Dockerfile` | desktop automation, screenshot, type, window control | stdio + HTTP (3012) | Read/Write | MED – privileged | [compose.yml desktop-commander](compose.yml); registry port 3012 |
| **Leantime Bridge (MCP)** | `docker/mcp-servers/leantime-bridge/Dockerfile` | PM integration (task CRUD, project sync) | HTTP | Read/Write | LOW | [compose.yml leantime-bridge](compose.yml); registry port 3015 |
| **LiteLLM** | `docker/mcp-servers/litellm/Dockerfile` | model routing (OpenAI/Anthropic/Gemini/XAI) | HTTP proxy | Read | LOW | [compose.yml litellm](compose.yml); port 4000 |
| **task-orchestrator (stdio fallback)** | [services/task-orchestrator/mcp_stdio.py](services/task-orchestrator/mcp_stdio.py) | same 6 tools listed in surface inventory section 4 | stdio | Read/Write | LOW | not in compose CMD; only invoked directly |

**Client-side MCP servers** declared in user `~/.claude/MCP_*.md` modules: PAL, ConPort, Serena, dope-context, Exa, GPT-Researcher (all already covered above), plus desktop-commander.

---

## 7. Plugin / Hook / Workflow Existing Surface Inventory

| Existing Surface | Path | Trigger | Mutates? | Receipt? | Safe for Reuse? | Evidence |
|---|---|---|---|---|---|---|
| `log_progress.sh` | `.claude/hooks/log_progress.sh` | SessionStart, UserPromptSubmit, PostToolUse | NO (log only) | stdout/file | YES | settings.json hooks block |
| `prompt_analyzer.py` | `.claude/hooks/prompt_analyzer.py` | UserPromptSubmit, PreToolUse | NO (analysis) | stdout/JSON | YES | settings.json |
| `session_lifecycle.py` | `.claude/hooks/session_lifecycle.py` | SessionStart, SessionEnd, Stop | YES (state save) | ConPort context save | YES (proven path) | settings.json |
| `track_file_edit.sh` | `.claude/hooks/track_file_edit.sh` | PostToolUse | NO (log) | file manifest | YES | settings.json |
| `check_energy.sh` | `.claude/hooks/check_energy.sh` | UserPromptSubmit, PreToolUse | NO (advisory) | stdout/warning | YES | settings.json |
| `save_context.sh` | `.claude/hooks/save_context.sh` | PostToolUse, PreCompact, SessionEnd | YES (ConPort save) | ConPort receipt | YES | settings.json |
| `native_hooks.py` (dispatcher) | `src/dopemux/claude/native_hooks.py` | all 10 lifecycle events route through this | dispatch | per-hook | YES (canonical dispatcher) | [.claude/settings.json](.claude/settings.json) lines 6–106 |
| `/save` slash command | `.claude/commands/save.md` | manual | YES (ConPort write) | yes | YES | save skill listed in available-skills |
| `/dx:implement`, `/dx:load`, `/dx:save` | per [.claude/CLAUDE.md SuperClaude block](.claude/CLAUDE.md) | manual | varies | varies | YES | .claude/CLAUDE.md lines 119–128 |
| `scripts/dopetask` | repo root scripts dir | direct invocation | YES (runs dopetask 0.5.1) | yes (dopetask emits) | YES (canonical) | [scripts/dopetask](scripts/dopetask) |
| `scripts/taskx` | repo root scripts dir | direct invocation | YES (via dopetask) | yes | DEPRECATING — shim only | [scripts/taskx](scripts/taskx); AGENTS.md §6 line 79 |
| `update_supervisor_for_dopetask.py` | `scripts/` | manual | YES (config write) | none observed | UNKNOWN | 4.6 KB file; not inspected fully |
| `/research:quick`, `/research:deep`, `/research:report` | `.claude/commands/research-*.md` | manual | NO (read-only) | research_id to ConPort | YES | available-skills list |
| `/security-review` | `.claude/commands/security-review.md` | manual | NO | none | YES | available-skills list |
| `/sc:*` (SuperClaude commands) | `.claude/commands/sc/` (inferred from available-skills) | manual | varies | varies | YES | available-skills list |
| `.claude/commands/dx/` | dx subdirectory | manual | varies | varies | YES | dir listing |

**Notable absence**: no slash command, hook, or skill currently invokes task-orchestrator directly. Operator interaction with task-orchestrator is mediated through (a) `src/dopemux/pm/` Python library calls (e.g., from `/save` or session hooks), or (b) `dopecon-bridge` proxy. There is no `/workflow:transition`, `/task-orch:*`, or equivalent operator surface.

---

## 8. Drift / Contradictions

| Drift | Evidence A | Evidence B | Risk | Recommended Handling |
|---|---|---|---|---|
| **task-orchestrator entrypoint conflict** | AGENTS.md §10: *"Task-orchestrator runtime authority is conflicted across `app/main.py`, `task_orchestrator/app.py`, and Docker wiring."* | `task_orchestrator/app.py` actually `sys.exit(1)` on import with "UNSUPPORTED RUNTIME" guard text; Dockerfile CMD calls `app.main:app` only | LOW (runtime resolved) | Update AGENTS.md §10 to acknowledge resolution; remove or shrink to "stale call sites may exist" |
| **task-orchestrator port 8000 vs 3014** | Dockerfile, compose.yml, registry.yaml, [src/dopemux/pm/adapters/orchestrator.py:15](src/dopemux/pm/adapters/orchestrator.py#L15) (explicit comment) all = 8000 | [services/mcp-integration-bridge/main.py:58](services/mcp-integration-bridge/main.py#L58) hardcodes `:3014`; PM_PLANE.md §4.2 doc text says *"defaults to `TASK_ORCHESTRATOR_URL=http://localhost:3014`"* | HIGH for `mcp-integration-bridge`; MED for doctrine | Fix `mcp-integration-bridge/main.py:58` to `:8000` (or use env var); update PM_PLANE.md §4.2 to match adapter (8000) |
| **`docker/compose.core.yml` absent** | SERVICE_CATALOG.md §2 line 30 cites it as "current runtime evidence"; INSTALL.md:240 documents it; multiple `out/` system docs reference it (15_SYSTEM_TASKORCHESTRATOR.md, 18_SYSTEM_DOPECONTEXT.md, 19_SYSTEM_DOPECONBRIDGE.md) | `find` for `compose.core.yml` returns nothing under `docker/`; `grep` returns no creation references | MED (only `compose.yml` ships) | Either create `docker/compose.core.yml` as the documented "essential infrastructure subset" or remove references from SERVICE_CATALOG.md and INSTALL.md |
| **scripts/taskx vs scripts/dopetask naming** | AGENTS.md §6 line 79: *"`scripts/taskx` is a compatibility shim"*; AGENTS.md §10: *"operator naming still drifts through TaskX language"* | scripts/taskx exists (164 bytes); does delegate to dopetask | LOW (functionally aligned) | Continue migration; consider deprecation notice in taskx shim |
| **ConPort port 3004 vs 3005** (NOT a conflict — intentional dual interface) | compose.yml maps both `3004:3004` (HTTP) and `3005:3005` (MCP/SSE) | But reader code uses 3005 for context and 3004 for decisions inside *same* PM concern family — PM_PLANE.md §4.1 calls this *"observed drift, not a single clean read contract"* | MED | Document the split in SERVICE_CATALOG.md or unify on one URL via shared client config |
| **dope-memory vs working-memory-assistant** | compose service `dope-memory` builds from `services/working-memory-assistant/Dockerfile.dope-memory` | Both are populated services dirs; AGENTS.md §10 flags *"Memory-related surfaces overlap across `dope_memory_main.py`, `main.py`, and `mcp/server.py`"* | MED (naming/role overlap) | Either rename `services/working-memory-assistant/` to `services/dope-memory/` or split working-memory-assistant into its own image |
| **adhd_engine vs adhd-engine spelling** | `services/adhd_engine/main.py` (real, populated, used by `services/adhd_engine/Dockerfile` in compose) | `services/adhd-engine/auth.py` (1 file, 1.25 KB stub) | LOW | Delete or quarantine `services/adhd-engine/` |
| **session-intelligence vs session_intelligence spelling** | `services/session-intelligence/bridge_adapter.py` (4 KB; has README) | `services/session_intelligence/coordinator.py` (1 file, test/demo) | LOW | Delete or quarantine `services/session_intelligence/` |
| **/info self-report "37 tools" vs 6 MCP tools** | task-orchestrator `app/main.py:372` claims `mcp_tool_count: 37` | `task_orchestrator/mcp/__init__.py:20–106` defines exactly 6 in `MCP_TOOLS` | LOW (cosmetic) | Fix self-report or compute dynamically |
| **DOPETASK_INTEGRATION_ANALYSIS.md "PARTIAL INTEGRATION"** (line 4, dated 2026-02-16) | Verdict: *"Orchestrator Bridge: 50% implemented, event emitter only, consumer incomplete"*; *"ConPort persistence callback NOT implemented"*; *"Task Packet system not notified of progress"* | Code at HEAD `7037c5f29` still shows ConPort consumer absent; coordinator emits to `dopecon-bridge` but no subscription wired back into task-orchestrator | HIGH for end-to-end ADHD workflow | Required before promoting task-orchestrator to operator-facing surface |
| **Agent runtime authority UNKNOWN** | AGENTS.md §6 final paragraph + §10 | Multiple agent families coexist (services/agents/*.py, src/dopemux/agent_orchestrator.py, services/task-orchestrator/task_orchestrator/agents/) | MED for governance clarity | Do not assume any agent path is canonical without explicit verification |
| **PM_PLANE.md §4.2 adapter URL** | Doc says default 3014 | Code says default 8000 (with explicit comment "Active runtime authority is app.main on port 8000 in this checkout") | LOW (runtime corrected, doc stale) | Update PM_PLANE.md §4.2 |
| **DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane** in task-orchestrator env | compose.yml:408 | env var labels task-orchestrator as `cognitive_plane` source for bridge routing; semantic meaning of the label not investigated | LOW | OBSERVED only — no judgment on whether label correctly reflects role |

---

## 9. Recommended Integration Boundaries

For integrating task-orchestrator into Dopemux daily operator workflows. Labels: **OBSERVED** = code shows it; **INFERRED** = strongly implied; **PROPOSED** = recommended change; **UNKNOWN** = needs decision; **RISK** = high-blast-radius; **REQUIRES_REPO_INSPECTION** = blocked on deeper read.

| Capability | Current Owner | task-orchestrator Should | Approval Needed | Failure Mode |
|---|---|---|---|---|
| **Workflow transitions** (state changes) | **OBSERVED**: task-orchestrator already canonical via `pm_transition_work_item` → `orchestrator_client.transition` | **OBSERVED**: continue owning; no change | none — already authoritative per AGENTS.md §6 | task-orchestrator down → transitions blocked (already true today) |
| **Operator-facing transition command** | **OBSERVED**: no slash command exists; operators call via `src/dopemux/pm/` library or hooks | **PROPOSED**: add `/workflow:transition`, `/workflow:queue`, `/workflow:blockers` slash commands that wrap `TaskOrchestratorAdapter` | YES — operator-surface change; [AGENTS.md §6 ADHD Engine "supports operator state … and hooks only"] does not forbid | misuse risk → wrap in confirmation per /save pattern |
| **Workflow ideas / epics CRUD** | **OBSERVED**: task-orchestrator HTTP + bridge custom-data | **OBSERVED**: continue; consider MCP tool wrappers for ADHD-friendly access | OPTIONAL — improves discoverability | bridge outage → no persistence |
| **Workflow event consumption** | **OBSERVED**: events emitted but NOT consumed ([DOPETASK_INTEGRATION_ANALYSIS.md](DOPETASK_INTEGRATION_ANALYSIS.md) line 115–120) | **PROPOSED**: implement event subscription to update ConPort progress and Task Packet status on transitions | YES — completes the integration that doctrine assumes exists | **RISK**: silent dropouts today; ConPort progress lags transitions |
| **PM metadata updates** | **OBSERVED**: Leantime canonical via `pm_update_work_item` | **OBSERVED**: task-orchestrator must NOT own; continue routing through `pm_update_work_item` | none | mis-routing → bypasses Leantime authority |
| **Decision / progress logging** | **OBSERVED**: ConPort canonical; mirrored to dope-memory | **OBSERVED**: task-orchestrator must NOT own; emit events that ConPort writers consume | none | **REQUIRES_REPO_INSPECTION**: where does ConPort subscribe to task-orchestrator events? Verdict: doesn't yet (per DOPETASK_INTEGRATION_ANALYSIS) |
| **Chronicle / receipts** | **OBSERVED**: dope-memory canonical via `memory_client.append_chronicle` | **OBSERVED**: task-orchestrator must NOT own | none | none for boundary |
| **Code & docs retrieval** | **OBSERVED**: dope-context | **OBSERVED**: task-orchestrator must NOT own | none | none |
| **MCP tool exposure for operator** | **OBSERVED**: 6 stdio MCP tools (analyze_dependencies, batch_tasks, get_adhd_state, get_task_recommendations, record_break, get_agent_status) | **PROPOSED**: keep current 6; consider promoting `get_priority_queue` / `get_blockers` / `transition_work_item` as MCP tools to match HTTP surface | YES — adds writable MCP tools; impacts permission model | new tools may need permission allowlisting in `.claude/settings.json` |
| **dopecon-bridge as router** | **OBSERVED**: routes events; persists task-orchestrator custom-data | **OBSERVED**: bridge stays as router/proxy ONLY per AGENTS.md §6 + §10 "Known Dangers" | none | **RISK**: bridge handler creep — periodic audit needed |
| **Agents calling task-orchestrator** | **UNKNOWN**: AGENTS.md §6 final paragraph + §10 — agent runtime authority unproven across families | **PROPOSED**: explicitly forbid agent direct writes to task-orchestrator unless agent runtime path is verified; route via `pm_transition_work_item` | YES — governance call; current state UNKNOWN per AGENTS.md | rogue agent write → bypasses canonical writer rules |
| **dopetask handoff for execution** | **OBSERVED**: `scripts/dopetask` (pinned 0.5.1) is canonical | **OBSERVED**: task-orchestrator should not invoke dopetask directly; doctrine is dopetask is execution-adjacent, not PM-adjacent | none | dopetask doctor non-main bug (script lines 86–95) |
| **Lifecycle hook integration** | **OBSERVED**: `session_lifecycle.py`, `save_context.sh` write ConPort context | **PROPOSED**: extend `session_lifecycle.py` to call `pm_get_priority_queue` / `pm_get_blockers` at SessionStart for "where you left off" ADHD UX | OPTIONAL — read-only enhancement; consistent with ADHD doctrine | adapter timeout (10 s) → SessionStart latency |
| **Operator startup orientation** | **OBSERVED**: `/sc:load` and ConPort `get_active_context` | **PROPOSED**: enrich orientation with task-orchestrator queue head + open blockers (read-only) | OPTIONAL | adapter failure → fall back to ConPort-only |
| **Workflow persistence backend** | **OBSERVED**: bridge custom-data categories `workflow_ideas`, `workflow_epics`, `workflow_audit` (NOT a local DB) | **REQUIRES_REPO_INSPECTION**: is this acceptable long-term? AGENTS.md §10 marks dopecon-bridge as a "Known Danger" | YES — architecture decision | bridge outage → workflow record loss |
| **Compose wiring** | **OBSERVED**: task-orchestrator depends_on `redis-primary, conport, leantime` (NOT dopecon-bridge despite using it via env var `DOPECON_BRIDGE_URL`) | **PROPOSED**: add `dopecon-bridge` to depends_on chain since `WorkflowService.save_custom_data` depends on it | YES — small change with healthcheck implications | startup race: task-orch becomes ready before bridge → first writes fail |
| **MCP integration bridge ghost client** | **OBSERVED**: `services/mcp-integration-bridge/main.py:58` hardcodes port 3014 (no longer the real port) | **PROPOSED**: either delete/quarantine `services/mcp-integration-bridge/` or fix line 58 to `:8000` (preferably env-var) | YES — confirms bridge is alive or dead | silent failure today; service is not in compose.yml |

---

## 10. Evidence Ledger

All commands run in this investigation; relevant output summarized below.

### Direct commands (exit codes captured where surfaced)

| # | Command | Exit | Output Summary |
|---|---|---|---|
| 1 | `pwd && git rev-parse --show-toplevel && git status --short && git branch --show-current && git rev-parse HEAD` | 0 | worktree path, clean status, branch `claude/beautiful-pascal-d3361e`, HEAD `7037c5f29` |
| 2 | `find . -maxdepth 3 -type f \( ... governance files \)` | 0 | Found: `AGENTS.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, `PROJECT.md`, `SERVICE_CATALOG.md`, `compose.yml`, `pyproject.toml`, `services/registry.yaml`, `services/session-manager/pyproject.toml`, `SYSTEM_ARCHIVE/genetic_agent_root_duplicate/pyproject.toml` — **NO** `SYSTEM_*.md` or `TRUTH_*.md` at depth ≤ 3 |
| 3 | `git remote -v` + `ls services/` | 0 | Both remotes point to `DDD-Enterprises/dopemux-mvp`; 46 service dirs enumerated |
| 4 | `ls services/task-orchestrator/` | 0 | 39 entries including `app/`, `task_orchestrator/`, `Dockerfile`, `mcp_stdio.py`, `server.py`, `query_server.py`, multiple test files |
| 5 | `cat services/registry.yaml | head -80` | 0 | Registry header + first ~10 service entries; format confirmed |
| 6 | `cat AGENTS.md` (full) | 0 | All §§ 1–10 captured verbatim |
| 7 | `sed -n '380,430p' compose.yml` | 0 | task-orchestrator service block: build, env (CONPORT_URL=…:3005, DOPECON_BRIDGE_URL=…:3016, PORT=8000), ports `${TASK_ORCHESTRATOR_PORT:-8000}:8000`, depends_on `[redis-primary, conport, leantime]`, healthcheck `localhost:8000/health` |
| 8 | `cat .dopetask-pin && cat .dopetaskroot && cat scripts/dopetask` | 0 | pin: install=pip, dep=dopetask, version=0.5.1; `.dopetaskroot` EMPTY (0 bytes); dopetask script: 98 lines — authority rails, pin parse, venv mgmt, exec |
| 9 | `find services/task-orchestrator -maxdepth 4 -name "app.py" -o -name "main.py"` | 1 (find non-fatal) | Both `task_orchestrator/app.py` AND `app/main.py` exist |
| 10 | `ls services/task-orchestrator/task_orchestrator/` | 0 | `__init__.py, adapters, adhd, agents, app.py, config.py, core.py, mcp, models.py` |
| 11 | `find . -maxdepth 4 -iname "dopetask*spec*"` | 1 | No file at root or shallow paths; **only canonical location is `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`** (referenced from 8+ proof bundles) |
| 12 | `grep -rn "dopetask-canonical-spec\|cannonical"` | 0 | AGENTS.md:42 + AGENTS.md:55 cite the schema; proof bundles use it; one `proof/repo-deep-remaining-work-audit-2026-05-02.proof.json` uses the misspelled `cannonical` |
| 13 | `head -30 task_orchestrator/app.py && head -30 app/main.py` | 0 | `task_orchestrator/app.py` = hard-fail stub with `sys.exit(1)` and guard text; `app/main.py` = real FastAPI coordination service |
| 14 | `cat PM_PLANE.md \| head -100` | 0 | §§ 1–4 captured — PM authority split, ConPort dual-URL drift, task-orchestrator workflow authority |
| 15 | `sed -n '100,160p' PM_PLANE.md` | 0 | §§ 5 PM write paths: metadata → Leantime; transitions → task-orchestrator; progress/decisions → ConPort + dope-memory mirror; workflow records → bridge custom-data |
| 16 | `grep -rn "TASK_ORCHESTRATOR_URL\|TaskOrchestratorAdapter" src/dopemux/` | 0 | `pm/adapters/orchestrator.py:15` and `:101` both default to `http://localhost:8000` with explicit comment "Active runtime authority is app.main on port 8000 in this checkout" |
| 17 | `head -40 src/dopemux/pm/adapters/orchestrator.py` | 0 | Confirms 8000 default; httpx client; routes for queue/blockers/state/transitions |
| 18 | `grep -n "3014\|3004\|3005" compose.yml \| head -20` | 0 | compose.yml:243 `MCP_SERVER_PORT=3005`; lines 253–254 publish 3004:3004 and 3005:3005; line 406 + 439 set `CONPORT_URL=http://conport:3005` |
| 19 | `grep -rn "3014" services/mcp-integration-bridge/` | 0 | `main.py:58` hardcodes `http://{CONTAINER_PREFIX}-task-orchestrator:3014` — stale port |
| 20 | `grep -A 8 "name: conport" services/registry.yaml \| head -25` | 0 | Two entries: `conport-http` (3004, smoke-enabled) and `conport-mcp` (3005, not in smoke) |
| 21 | `grep -n "^##\|^#" DOPETASK_INTEGRATION_ANALYSIS.md \| head -40` + `head -20` | 0 | Document dated 2026-02-16; verdict line 4: "⚠️ PARTIAL INTEGRATION - Systems exist but lack end-to-end coordination"; table at line 14: Orchestrator Bridge 50% implemented / event emitter only |
| 22 | `find ... -name "compose.core.yml"` + `ls docker/` | 0 | docker/ contains: conport-kg, leantime, mcp-servers, mcp-servers-source, postgres — **NO compose.core.yml** anywhere |
| 23 | `grep -rn "compose.core.yml"` | 0 | Referenced by SERVICE_CATALOG.md:30, INSTALL.md:240, multiple `out/` and `proof/` artifacts; **file does not exist on disk** — known doc/runtime drift |
| 24 | `head -80 SERVICE_CATALOG.md` | 0 | Tier 1 services list; cites missing `docker/compose.core.yml` |
| 25 | `Read services/task-orchestrator/app/main.py offset=300 limit=200` | 0 | Spot-verified Section 4 line numbers: /health@307, /info@350, /metrics@380, /api/workflow/ideas POST@441, GET@455, PATCH@469, promote@483; self-report `"tools_count": 37` confirmed at line 372 |

### Files inspected (paths only)

**Governance & authority docs**:
- [AGENTS.md](AGENTS.md) — full read; all 10 sections
- [PM_PLANE.md](PM_PLANE.md) — §§ 1–5 (lines 1–160)
- [SERVICE_CATALOG.md](SERVICE_CATALOG.md) — §§ 1–4 (lines 1–80)
- [PROJECT.md](PROJECT.md) — head + task-orchestrator section
- [ARCHITECTURE.md](ARCHITECTURE.md) — head + task-orchestrator references

**task-orchestrator runtime**:
- [services/task-orchestrator/Dockerfile](services/task-orchestrator/Dockerfile) — full content
- [services/task-orchestrator/app/main.py](services/task-orchestrator/app/main.py) — head + route map (offset 300, limit 200 verified)
- [services/task-orchestrator/task_orchestrator/app.py](services/task-orchestrator/task_orchestrator/app.py) — full content (15 lines, hard-fail stub)
- [services/task-orchestrator/task_orchestrator/](services/task-orchestrator/task_orchestrator/) — dir listing
- [services/task-orchestrator/mcp_stdio.py](services/task-orchestrator/mcp_stdio.py) — full content (3 lines)

**PM plane adapters**:
- [src/dopemux/pm/adapters/orchestrator.py](src/dopemux/pm/adapters/orchestrator.py) — head (lines 1–40)
- [src/dopemux/pm/writes.py](src/dopemux/pm/writes.py) — referenced via PM_PLANE.md citations
- [src/dopemux/pm/reads.py](src/dopemux/pm/reads.py) — referenced via PM_PLANE.md citations

**Container/registry wiring**:
- [compose.yml](compose.yml) — task-orchestrator block (lines ~380–430); ConPort block (lines ~232–266); port-relevant lines via grep
- [services/registry.yaml](services/registry.yaml) — head + conport entries (via grep)
- [pyproject.toml](pyproject.toml) — `[project.scripts]` (lines 136–141)
- [docker/](docker/) — directory listing (5 subdirs, NO compose.core.yml)

**Scripts**:
- [scripts/dopetask](scripts/dopetask) — full content
- [scripts/taskx](scripts/taskx) — full content
- [.dopetask-pin](.dopetask-pin) — full (3 lines)
- [.dopetaskroot](.dopetaskroot) — empty marker file (0 bytes)

**Drift evidence**:
- [services/mcp-integration-bridge/main.py:58](services/mcp-integration-bridge/main.py#L58) — stale `:3014` URL
- [DOPETASK_INTEGRATION_ANALYSIS.md](DOPETASK_INTEGRATION_ANALYSIS.md) — head + section index (2026-02-16 dated)
- `out/chatgpt-project-upload-set/.../04_SYSTEM_BOUNDARIES.md` — confirms compose.core.yml absence
- `out/chatgpt-project-upload-set/.../15_SYSTEM_TASKORCHESTRATOR.md` — confirms port 8000

### Agent reports synthesized (3 parallel Explore agents)

1. **Task-orchestrator deep-dive** — surface inventory, ports, MCP tools, storage, dependencies, Dockerfile/app/main.py reconciliation, tests, scripts.
2. **PM plane + adjacent services** — service catalog with canonical writers per concern, boundary map, drift checks (dope-memory vs WMA, adhd_engine spellings, session_intelligence spellings, dopecon-bridge authority).
3. **Compose/registry/governance** — compose.yml service table, registry entries, MCP server inventory, hooks/commands/scripts, AGENTS.md quotes, PM_PLANE.md / PROJECT.md / ARCHITECTURE.md role claims, drift indicators.

### Confidence and unknowns

- Confidence: **HIGH** for runtime entrypoints, port assignments, canonical writers, AGENTS.md authority quotes.
- Confidence: **MEDIUM** for completeness of agent inventory (services/agents/ has 17 files; full role mapping not exhaustive).
- Confidence: **MEDIUM** for event-bus subscription state (DOPETASK_INTEGRATION_ANALYSIS.md is 3 months old; current state of ConPort consumer wiring inferred from absence in current `services/task-orchestrator/` files).
- **UNKNOWN**: full repo-truth-extractor runtime topology (no HTTP main.py found).
- **UNKNOWN**: full plugin manifest for dope-context autonomous indexers (referenced in tools, daemon entrypoint not located).
- **UNKNOWN**: whether `services/mcp-integration-bridge/` is intentionally retired or accidentally orphaned.

### Final repo-truth verdict

**task-orchestrator is wired, authorized, and operationally narrow.** It owns workflow transitions (HTTP `POST /api/projects/{id}/workflow/transition` and `POST /api/pm/work-items/{id}/transition`) and serves workflow queue/blockers/state reads. It does NOT own PM metadata (Leantime), structured decisions/progress (ConPort), chronicle (dope-memory), or code retrieval (dope-context). Its workflow record persistence is bridge-mediated (custom-data categories) rather than a local DB — a real but documented architectural choice.

**Integration into daily operator workflows is currently mediated by Python library calls** (`src/dopemux/pm/`) — no slash commands or MCP tools expose `transition` / `queue` / `blockers` to operators directly. The biggest gap is the missing event consumer side of the two-plane integration (`DOPETASK_INTEGRATION_ANALYSIS.md` confirms emitter-only state).

**Known repo drifts**: `mcp-integration-bridge/main.py:58` ghost client at `:3014`; `docker/compose.core.yml` referenced everywhere but absent; PM_PLANE.md §4.2 cites `:3014` (adapter says `:8000`); ConPort context vs decision URL split inside same integration; dope-memory image built from working-memory-assistant Dockerfile; `services/adhd-engine/` and `services/session_intelligence/` are 1-file stubs of populated underscore variants.
