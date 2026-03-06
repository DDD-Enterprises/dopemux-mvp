# S7 — Overseer : Agent Flow Design

## 1. Document Purpose

This document synthesizes the overseer→agent architecture from integration surfaces extracted across the dopemux-mvp repository. It connects the `AgentManager` orchestration core to its agent types, lifecycle states, hook contracts, event flows, editor integrations, and service dependencies.

**Source Artifacts (synthesized from codebase extraction):**

- `EDITOR_INTEGRATION_SURFACE` — Editor/IDE config bindings (Claude Code, Copilot CLI, Vibe)
- `HOOK_CONTRACT_SURFACE` — Hook trigger→handler mappings with transport classification
- `EVENT_FLOW_GRAPH` — Event type definitions, pub/sub topology, adapter contracts
- `AGENT_ORCHESTRATION_SURFACE` — AgentType enum, AgentManager methods, lifecycle FSM
- `SERVICE_CATALOG` — Infrastructure, MCP, coordination, and cognitive service registry

**Failure Mode Note:** The pre-computed JSON artifacts (`EDITOR_INTEGRATION_SURFACE.json`, `HOOK_CONTRACT_SURFACE.json`, `EVENT_FLOW_GRAPH.json`, `AGENT_ORCHESTRATION_SURFACE.json`, `SERVICE_CATALOG.json`) were not available as upstream outputs. This synthesis was produced by direct codebase extraction against the same source scopes defined in prompts A11, A13, C10, and C12.

---

## 2. Architecture Overview

Dopemux implements a **multi-level overseer→agent orchestration** pattern with three structural layers:

```
┌──────────────────────────────────────────────────────────┐
│                    EDITOR LAYER                          │
│  Claude Code │ Copilot CLI │ Vibe Agents                │
│  (hooks, MCP bindings, instruction surfaces)             │
└──────────┬───────────────────────────┬───────────────────┘
           │                           │
           ▼                           ▼
┌──────────────────────┐   ┌───────────────────────────────┐
│   HOOK SYSTEM        │   │   MCP BROKER (MetaMCPBroker)  │
│  Claude Code Hooks   │   │   Tool dispatch + budget      │
│  Git Hooks           │   │   Role switching (<200ms)     │
│  Shell Hooks         │   │   Session checkpointing       │
│  EventBus            │   │   Discovery gate (Phase 0)    │
└──────────┬───────────┘   └──────────┬────────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────────────────────────────────────────┐
│              AGENT ORCHESTRATION CORE                    │
│  AgentManager → AgentType dispatch → AgentWorkflow      │
│  Priority queue │ Daemon worker │ Sync execution         │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────────┐   ┌──────────────────────────────┐
│  COGNITIVE AGENTS    │   │  COORDINATION SERVICES        │
│  CognitiveGuardian   │   │  DopeconBridge (3016)         │
│  MemoryAgent         │   │  TaskOrchestrator (8000)      │
│  TaskDecomposer      │   │  ADHDEngine (8095)            │
│  ToolOrchestrator    │   │  DopeMemory (3020)            │
│  WorkflowCoordinator │   │  TwoPlaneOrchestrator         │
└──────────────────────┘   └──────────────────────────────┘
```

EVIDENCE: `src/dopemux/agent_orchestrator.py#AgentType` (L36-43), `src/dopemux/mcp/broker.py#MetaMCPBroker` (L164-450), `services/registry.yaml#services`

---

## 3. Agent Type Registry

All agent types are defined in the `AgentType` enum.

| Agent Type | Enum Value | Implementation | Role |
|---|---|---|---|
| `COGNITIVE_GUARDIAN` | `"cognitive_guardian"` | `services/agents/cognitive_guardian.py` | ADHD accommodation, energy/attention monitoring, break enforcement |
| `CUSTOM` | `"custom"` | Dynamic registration | User-defined agent logic |
| `MEMORY_AGENT` | `"memory_agent"` | `services/agents/memory_agent.py` | Session state persistence, checkpointing, interruption recovery |
| `TASK_DECOMPOSER` | `"task_decomposer"` | `services/agents/task_decomposer.py` | Task breakdown, subtask routing to planes, complexity assessment |
| `TOOL_ORCHESTRATOR` | `"tool_orchestrator"` | `services/agents/tool_orchestrator.py` | Model selection, tool routing, cost/latency estimation |
| `WORKFLOW_COORDINATOR` | `"workflow_coordinator"` | `services/agents/workflow_coordinator.py` | Multi-step workflow execution, templated sequences, auto-checkpointing |

EVIDENCE: `src/dopemux/agent_orchestrator.py#AgentType` (L36-43)

---

## 4. Agent Lifecycle Model

### 4.1 Agent Status FSM

States are defined in the `AgentStatus` enum.

```
                  submit_task()
    [IDLE] ──────────────────────► [RUNNING]
                                      │
                              ┌───────┴───────┐
                              │               │
                    success   ▼      error    ▼
                         [COMPLETED]      [ERROR]
                                            │
                                   retry    │
                                    ┌───────┘
                                    ▼
                                [RUNNING]

    [RUNNING] ──pause()──► [PAUSED] ──resume()──► [RUNNING]
```

| State | Value | Transitions To | Trigger |
|---|---|---|---|
| `COMPLETED` | `"completed"` | — | Task execution success |
| `ERROR` | `"error"` | `RUNNING` | Retry after failure |
| `IDLE` | `"idle"` | `RUNNING` | `submit_task()` call |
| `PAUSED` | `"paused"` | `RUNNING` | `resume()` call |
| `RUNNING` | `"running"` | `COMPLETED`, `ERROR`, `PAUSED` | Task dispatch, `pause()`, error |

EVIDENCE: `src/dopemux/agent_orchestrator.py#AgentStatus` (L27-33)

### 4.2 MCP Broker Lifecycle

```
    [STARTING] ──Phase0:DiscoveryGate──► [config load] ──► [init components]
        ──► [server connections] ──► [background tasks] ──► [HTTP server] ──► [READY]

    [READY] ──degradation──► [DEGRADED]
    [READY] ──maintenance──► [MAINTENANCE]
    [READY] ──fatal──► [FAILED]
```

| State | Value | Description |
|---|---|---|
| `DEGRADED` | `"degraded"` | Partial functionality available |
| `FAILED` | `"failed"` | Unrecoverable failure |
| `MAINTENANCE` | `"maintenance"` | Planned downtime |
| `READY` | `"ready"` | All systems operational |
| `STARTING` | `"starting"` | Initialization in progress |

EVIDENCE: `src/dopemux/mcp/broker.py#BrokerStatus` (L46-53), `src/dopemux/mcp/broker.py#start` (L259-298)

### 4.3 Session Lifecycle (ADHD-Optimized)

```
    [NEW] ──start_session()──► [ACTIVE] ──auto_save(30s)──► [CHECKPOINT]
                                   │                            │
                                   ▼                            │
                             [INTERRUPTED] ◄──restore_session()─┘
                                   │
                              end_session()
                                   ▼
                              [FINALIZED]
```

- Auto-save interval: 30 seconds
- Checkpoint includes: `current_task`, `current_focus`, `mode`, `open_files`, `cursor_positions`, `recent_decisions`, `next_steps`, `complexity`, `energy_level`, `attention_state`

EVIDENCE: `services/agents/memory_agent.py#SessionState` (L30-46), `services/agents/memory_agent.py#auto_save_interval` (L71-72)

---

## 5. AgentManager — Overseer Core

### 5.1 Class Structure

The `AgentManager` class (Lines 88–456 in `agent_orchestrator.py`) is the central overseer that dispatches tasks to registered agents via a priority-based internal queue.

| Method | Signature | Purpose |
|---|---|---|
| `_execute_agent_task()` | Dispatches by `agent_config.agent_type` | Route task to correct agent handler |
| `_process_tasks()` | `_process_tasks(self) → None` | Main daemon loop (0.1s sleep cycle) |
| `register_agent()` | `register_agent(self, config: AgentConfig) → None` | Register agent in `self._agents` dict |
| `register_agent_from_config()` | Loads YAML config | YAML-based agent registration |
| `start()` | `start(self) → None` | Spawn daemon thread `AgentOrchestratorWorker` |
| `stop()` | `stop(self) → None` | Stop worker with 5s timeout |
| `submit_task()` | `submit_task(self, task: AgentTask) → str` | Enqueue task, return UUID task_id |

### 5.2 Task Dispatch Flow

```
submit_task(AgentTask)
    │
    ▼
_task_queue.append(task)        # Priority-based list
    │
    ▼
_process_tasks() daemon loop
    │
    ▼
min(_task_queue, key=priority)  # Select highest priority
    │
    ▼
_execute_agent_task(task)       # Dispatch by agent_type
    │
    ├── TASK_DECOMPOSER     → TaskDecomposer.decompose_task()
    ├── TOOL_ORCHESTRATOR   → ToolOrchestrator.select_tool()
    ├── MEMORY_AGENT        → MemoryAgent.checkpoint()
    ├── COGNITIVE_GUARDIAN   → CognitiveGuardian.check_break_needed()
    ├── WORKFLOW_COORDINATOR → WorkflowCoordinator.execute_step()
    └── CUSTOM              → dynamic handler
```

### 5.3 Spawn Pattern

The overseer spawns a single daemon worker thread:

```python
self._worker_thread = threading.Thread(
    target=self._process_tasks,
    daemon=True,
    name="AgentOrchestratorWorker"
)
self._worker_thread.start()
```

EVIDENCE: `src/dopemux/agent_orchestrator.py#AgentManager` (L88-456), spawn pattern (L108-113), priority selection (L216)

---

## 6. Agent Definitions

### 6.1 CognitiveGuardian

Monitors user cognitive state and enforces ADHD-safe work boundaries.

| Aspect | Detail |
|---|---|
| **Attention States** | `FOCUSED`, `HYPERFOCUS`, `SCATTERED` |
| **Energy Levels** | `HIGH`, `LOW`, `MEDIUM` |
| **Break Enforcement** | Pomodoro: 25-min intervals, 90-min mandatory breaks |
| **Key Methods** | `check_break_needed()`, `check_task_readiness()`, `get_user_state()`, `start_monitoring()`, `suggest_tasks()` |
| **Persistence** | User state saved to ConPort via `_save_user_state()` |

EVIDENCE: `services/agents/cognitive_guardian.py#AttentionState` (L68-100)

### 6.2 MemoryAgent

Manages session state with auto-checkpointing for interruption resilience.

| Aspect | Detail |
|---|---|
| **Session Modes** | `"architect"`, `"ask"`, `"code"`, `"research"` |
| **Auto-Save** | Every 30 seconds (background) |
| **Key Methods** | `end_session()`, `restore_session()`, `start_session()` |
| **Tracked State** | `attention_state`, `complexity`, `current_focus`, `current_task`, `cursor_positions`, `energy_level`, `next_steps`, `open_files`, `recent_decisions`, `time_invested_minutes` |
| **Persistence** | ConPort MCP client |

EVIDENCE: `services/agents/memory_agent.py#SessionState` (L30-46)

### 6.3 TaskDecomposer

Breaks complex tasks into subtasks and routes them across planes.

| Aspect | Detail |
|---|---|
| **Task Types** | `DEBUGGING`, `DESIGN`, `DOCUMENTATION`, `IMPLEMENTATION`, `REFACTORING`, `RESEARCH`, `TESTING`, `UNKNOWN` |
| **Integrations** | CognitiveGuardian (validation), ConPort (logging), MemoryAgent (state), ToolOrchestrator (tool assignment), TwoPlaneOrchestrator (routing) |
| **Key Methods** | `_assign_tools_to_subtasks()`, `_integrate_with_memory_agent()`, `_log_decomposition_to_conport()`, `_route_subtasks_to_planes()`, `_validate_subtasks_with_guardian()`, `decompose_task()` |

EVIDENCE: `services/agents/task_decomposer.py#TaskType` (L31-40)

### 6.4 ToolOrchestrator

Selects models and tools based on task complexity and cost constraints.

| Aspect | Detail |
|---|---|
| **Complexity Tiers** | `COMPLEX` (0.7–1.0), `MEDIUM` (0.3–0.7), `SIMPLE` (0.0–0.3) |
| **Model Tiers** | `FAST` (low cost), `MID` (balanced), `POWER` (maximum capability) |
| **Selection Output** | `ToolSelection`: `estimated_cost`, `estimated_latency`, `fallback_tool`, `method`, `model`, `primary_tool`, `workspace_path` |

EVIDENCE: `services/agents/tool_orchestrator.py#TaskComplexity` (L67-80)

### 6.5 TwoPlaneOrchestrator

Routes requests between PM plane (Leantime) and Cognitive plane (AI agents).

| Aspect | Detail |
|---|---|
| **Planes** | `COGNITIVE` (AI agents), `PM` (Leantime project management) |
| **Request Types** | `COMMAND` (state-changing), `EVENT` (notification), `QUERY` (read-only) |
| **Authority** | `AuthorityRule` enforcement on cross-plane requests |
| **Transport** | DopeconBridge HTTP bridge |

EVIDENCE: `services/agents/two_plane_orchestrator.py#Plane` (L25-80)

### 6.6 WorkflowCoordinator

Executes multi-step workflows with auto-checkpointing.

| Aspect | Detail |
|---|---|
| **Workflow Types** | `ARCHITECTURE_DECISION`, `BUG_INVESTIGATION`, `CODE_REVIEW`, `CUSTOM`, `FEATURE_IMPLEMENTATION`, `REFACTORING` |
| **Key Methods** | `_create_checkpoint()`, `complete_workflow()`, `execute_step()`, `get_workflow_status()`, `initialize()`, `start_workflow()` |
| **Checkpoint** | Auto-save via MemoryAgent after each step |

EVIDENCE: `services/agents/workflow_coordinator.py#WorkflowType` (L25-32)

---

## 7. Communication Protocols

| Protocol | Source | Target | Mechanism | Direction |
|---|---|---|---|---|
| **Broker HTTP** | MCP Clients | MetaMCPBroker | aiohttp server | request_response |
| **ConPort MCP** | All Agents | ConPort Service | Async method calls (asyncpg + pgvector) | request_response |
| **Direct Agent Calls** | WorkflowCoordinator | MemoryAgent | `await self.memory_agent.create_checkpoint()` | request_response |
| **DopeconBridge HTTP** | TwoPlaneOrchestrator | Leantime / Agents | HTTP REST (port 3016) | request_response |
| **EventBus (InMemory)** | Any Publisher | Pattern Subscribers | `InMemoryAdapter` with pattern matching | pub_sub |
| **EventBus (Redis Streams)** | Any Publisher | Distributed Subscribers | `RedisStreamsAdapter` with fan-out | pub_sub |
| **Session Checkpoint** | MetaMCPBroker | SessionState | Context checkpoint on role switch | producer_to_consumer |
| **Task Queue** | AgentManager | Worker Thread | `List[AgentTask]` + priority selection | producer_to_consumer |

EVIDENCE: `src/dopemux/event_bus.py#InMemoryAdapter` (L82-132), `src/dopemux/event_bus.py#RedisStreamsAdapter` (L134-182), `src/dopemux/mcp/broker.py#call_tool` (L433-450)

---

## 8. Hook Contract Surface

### 8.1 Internal Hooks (HookManager)

| Hook Type | Enabled | Transport | Lifecycle Phase | Handler Path | Direction |
|---|---|---|---|---|---|
| `file-watch` | ✗ Experimental | `file_watch` | `on_message` | Not implemented | producer_to_consumer |
| `git-commit` | ✗ Disabled | `direct_call` | `on_complete` | `_handle_git_commit` | producer_to_consumer |
| `pane-focus` | ✓ | `direct_call` | `on_message` | `_handle_pane_focus` | producer_to_consumer |
| `save` | ✓ | `direct_call` | `on_message` | `_handle_file_save` | producer_to_consumer |
| `terminal-open` | ✓ | `direct_call` | `post_launch` | `_handle_terminal_open` | producer_to_consumer |

**Safety Guarantees:** Silent operation (`quiet_mode=True`), background processing (`asyncio.create_task()`), error isolation (exceptions caught, never propagate), timeout enforcement (100ms default, configurable 50–500ms).

EVIDENCE: `src/dopemux/hooks/hook_manager.py` (L78-127, L215-255)

### 8.2 Claude Code Hooks (.claude/hooks/)

| Hook Script | Trigger | Transport | Lifecycle Phase | Target Endpoint | Direction |
|---|---|---|---|---|---|
| `check_energy.sh` | PreToolUse (complex tools) | `webhook` | `pre_launch` | `GET/POST $ADHD_ENGINE_URL/state` | request_response |
| `log_progress.sh` | PostToolUse (all) | `webhook` | `on_complete` | `POST $ADHD_ENGINE_URL/record-progress` | producer_to_consumer |
| `prompt_analyzer.py` | UserPromptSubmit | `webhook` | `on_message` | Multiple: `/state`, `/unfinished-work`, `/log-intent`, `/save-context` | request_response |
| `save_context.sh` | Stop (session end) | `webhook` | `on_complete` | `POST $ADHD_ENGINE_URL/save-context` | producer_to_consumer |

**Complex Tool Pattern Match:** `thinkdeep|morph|batch_edit|refactor|deep_research`

EVIDENCE: `.claude/hooks/check_energy.sh`, `.claude/hooks/log_progress.sh`, `.claude/hooks/prompt_analyzer.py` (L1-316), `.claude/hooks/save_context.sh`

### 8.3 Claude Code External Monitor

| Monitor | Trigger | Transport | Lifecycle Phase | Direction |
|---|---|---|---|---|
| `file_change` | File mtime < 10s | `mcp_tool` | `on_message` | producer_to_consumer |
| `git_commit` | Recent commits < 2min | `mcp_tool` | `on_complete` | producer_to_consumer |
| `session_start` | Claude Code process alive (`pgrep`) | `mcp_tool` | `post_launch` | producer_to_consumer |
| `shell_command` | Claude-prefixed shell commands | `mcp_tool` | `on_message` | producer_to_consumer |

Poll interval: 2.0 seconds. Status persisted to `~/.dopemux/hook_status.json`.

EVIDENCE: `src/dopemux/hooks/claude_code_hooks.py` (L107-283)

### 8.4 Git Hooks

| Hook | Trigger | Transport | Lifecycle Phase | Handler | Direction |
|---|---|---|---|---|---|
| `pre-commit` | `git commit` | `direct_call` | `pre_launch` | `scripts/repo_preflight.sh` | request_response |

EVIDENCE: `.githooks/pre-commit` (L1-8)

### 8.5 MCP Pre-Tool Hooks

| Optimization | Action | Trigger Condition |
|---|---|---|
| `CACHE_RESULT` | Return cached value | Identical recent call |
| `DENY_EXPENSIVE` | Block execution | Hard budget cap reached |
| `REDUCE_SCOPE` | Narrow query scope | Budget near cap (90%) |
| `SUGGEST_ALTERNATIVE` | Offer cheaper tool | Budget warning (80%) |
| `TRIM_RESULTS` | Reduce output size | Budget threshold |

EVIDENCE: `src/dopemux/mcp/hooks.py` (L30-34, L92-150)

---

## 9. Event Flow Graph

### 9.1 Event Types

| Event Type | Actions | Source Component |
|---|---|---|
| `ADHDEvent` | `ATTENTION`, `BREAK_REMINDER`, `CONTEXT_SWITCH`, `ENERGY` | ADHD Engine |
| `ContextEvent` | `DECISION_LOGGED`, `PROGRESS_UPDATED`, `RESTORED`, `UPDATED` | ConPort |
| `SessionEvent` | `ATTACHED`, `CREATED`, `DESTROYED`, `DETACHED`, `LAYOUT_CHANGED`, `PANE_CREATED` | tmux orchestrator |
| `ThemeEvent` | `INTERPOLATED`, `SWITCHED`, `UPDATED` | Theme system |
| `WorktreeEvent` | `CLEANED`, `CREATED`, `REMOVED`, `SWITCHED` | Git worktree ops |

EVIDENCE: `src/dopemux/events/types.py` (L36-115)

### 9.2 EventBus Contract

```python
async def publish(event: DopemuxEvent) → bool
async def subscribe(pattern: str, callback: Callable) → str
async def unsubscribe(subscription_id: str) → None
```

**Pattern Matching:**
- Exact: `namespace == pattern`
- Prefix: `pattern="dopemux:*"` → matches all `dopemux:*` events
- Wildcard: `pattern="*"` → matches all events

**Event Envelope:**
- `type: str` — Event identifier
- `priority: EventPriority` — `CRITICAL`, `HIGH`, `LOW`, `NORMAL`
- `data: Dict[str, Any]` — Extensible payload
- `source: Optional[str]` — Emitting component
- `adhd_metadata: ADHDMetadata` — `can_batch`, `focus_required`, `interruption_allowed`, `time_sensitive`

EVIDENCE: `src/dopemux/event_bus.py` (L21-76, L82-182)

### 9.3 Transport Adapters

| Adapter | Pattern | Persistence | Distribution |
|---|---|---|---|
| `InMemoryAdapter` | pub_sub with pattern matching | None (process-local) | Single process |
| `RedisStreamsAdapter` | pub_sub with distributed fan-out | Redis Streams | Multi-process |

EVIDENCE: `src/dopemux/event_bus.py#InMemoryAdapter` (L82-132), `src/dopemux/event_bus.py#RedisStreamsAdapter` (L134-182)

### 9.4 End-to-End Event Flow

```
User Input
  │
  ├─► Claude Code Hook: prompt_analyzer.py
  │     ├─► GET  /adhd-engine/state          (energy/attention check)
  │     ├─► GET  /adhd-engine/unfinished-work (task conflict detection)
  │     ├─► POST /adhd-engine/log-intent      (ConPort audit)
  │     └─► Return: contextInjection → Claude
  │
  ├─► Tool Execution
  │     ├─► MCP PreToolHook: pre_tool_check()
  │     │     └─► OptimizationResult (CACHE/DENY/REDUCE/SUGGEST/TRIM)
  │     ├─► MetaMCPBroker.call_tool()
  │     │     ├─► Budget enforcement
  │     │     ├─► Role-based access control
  │     │     └─► Performance monitoring
  │     └─► Claude PostToolUse: log_progress.sh
  │           └─► POST /adhd-engine/record-progress
  │
  ├─► File Operations
  │     ├─► HookManager: save hook
  │     │     └─► _handle_file_save → _index_file_background (async)
  │     └─► ClaudeCodeMonitor: file_change
  │           └─► _batch_index_files (async)
  │
  ├─► Agent Task Submission
  │     ├─► AgentManager.submit_task()
  │     │     └─► _task_queue (priority-sorted)
  │     ├─► _process_tasks() daemon loop
  │     │     └─► _execute_agent_task() → agent dispatch
  │     └─► AgentWorkflow (multi-step)
  │           └─► Sequential submit_task() per step
  │
  └─► Session Completion
        └─► Claude Stop Hook: save_context.sh
              └─► POST /adhd-engine/save-context
```

---

## 10. Editor Integration Bindings

### 10.1 Active Editor Surfaces

| Editor | Status | Primary Config | MCP Server Count | Transport |
|---|---|---|---|---|
| **Claude Code** | Active | `.claude/claude_config.json` | 11+ | stdio + HTTP proxy |
| **Copilot CLI** | Active | `.github/copilot-instructions.md`, `mcp-proxy-config.copilot.yaml` | 10+ | stdio |
| **Vibe Agents** | Active | `.vibe/agents/*.toml` | 10+ | HTTP (ports 3003–8095) |

### 10.2 Inactive Editor Surfaces

| Editor | Status | Evidence |
|---|---|---|
| **Cursor** | Not configured | No `.cursor/` directory found |
| **EditorConfig** | Not configured | No `.editorconfig` file found |
| **VS Code** | Not configured | No `.vscode/` directory found |

EVIDENCE: `.claude/claude_config.json`, `.vibe/agents/tp-dev.toml`, `mcp-proxy-config.copilot.yaml`

### 10.3 MCP Server Bindings per Editor

| MCP Server | Claude Code | Copilot CLI | Vibe Agents | Transport |
|---|---|---|---|---|
| `conport` | ✓ (stdio: docker exec) | ✓ (stdio: docker exec) | ✓ (HTTP: 3005) | stdio / HTTP |
| `context7` | ✓ (stdio: npx) | — | — | stdio |
| `conport-admin` | ✓ (stdio: docker exec) | — | — | stdio |
| `dope-context` | ✓ (stdio: bash script) | ✓ (stdio) | ✓ (HTTP: 3010) | stdio / HTTP |
| `dope-memory` | — | — | ✓ (HTTP: 3020) | HTTP |
| `exa` | ✓ (stdio: uvx proxy) | ✓ (stdio) | ✓ (HTTP: 3007) | stdio / HTTP |
| `gpt-researcher` | ✓ (stdio: event wrapper) | ✓ (stdio: event wrapper) | ✓ (HTTP: 3009) | stdio / HTTP |
| `leantime-bridge` | — | — | ✓ (HTTP: 3014) | HTTP |
| `mas-sequential-thinking` | ✓ (stdio: docker exec) | — | — | stdio |
| `pal` | ✓ (stdio: uvx) | ✓ (stdio: uvx) | ✓ (HTTP: 3003) | stdio / HTTP |
| `serena` | ✓ (stdio: uvx proxy) | — | ✓ (HTTP: 3006) | stdio / HTTP |
| `task-orchestrator` | ✓ (stdio: python) | ✓ (stdio) | ✓ (HTTP: 8000) | stdio / HTTP |
| `zen` | ✓ (stdio: uvx) | — | — | stdio |

EVIDENCE: `.claude/claude_config.json`, `mcp-proxy-config.copilot.yaml`, `.vibe/agents/tp-dev.toml`

### 10.4 Workspace-Aware MCP Routing

The MCP proxy layer supports workspace-scoped routing for multi-workspace isolation.

| Server | Workspace-Aware | Parameter |
|---|---|---|
| `conport` | ✓ | `workspace_id` |
| `dope-context` | ✓ | `workspace_path` |
| `exa` | ✗ | — |
| `mas-sequential-thinking` | ✗ | — |
| `pal` | ✓ | `workspace_path` |
| `serena` | ✓ | `workspace_path` |
| `task-orchestrator` | ✓ | `workspace_id` |

EVIDENCE: `mcp-proxy-config.yaml#mcp_servers`

---

## 11. Service Dependency Map

### 11.1 Infrastructure Layer

| Service | Port | Category | Health | Downstream Dependents |
|---|---|---|---|---|
| `litellm` | 4000 | infrastructure | `GET /health` | ToolOrchestrator model routing |
| `postgres` | 5432 | infrastructure | `pg_isready` | conport, dopecon-bridge, dope-memory |
| `qdrant` | 6333 | infrastructure | `GET /` | conport, dope-context, dopecon-bridge, leantime-bridge |
| `redis-events` | 6379 | infrastructure | `redis-cli ping` | dopecon-bridge, dope-memory (EventBus RedisStreamsAdapter) |
| `redis-primary` | 6380 | infrastructure | `redis-cli ping` | adhd-engine, task-orchestrator |

### 11.2 MCP Layer

| Service | Port | Category | Health | Role |
|---|---|---|---|---|
| `conport-http` | 3004 | mcp | `GET /health` | Knowledge graph HTTP API |
| `conport-mcp` | 3005 | mcp | `GET /health` | Knowledge graph MCP (SSE) |
| `desktop-commander` | 3012 | mcp | `GET /health` | Desktop automation |
| `dope-context` | 3010 | mcp | `GET /health` | Semantic code/docs search |
| `dope-memory` | 3020 | mcp | `GET /health` | Temporal chronicle, working memory |
| `exa` | 3011 | mcp | `GET /health` | Neural web search |
| `gpt-researcher` | 3009 | mcp | `GET /health` | Deep web research |
| `pal` | 3003 | mcp | `GET /health` | Multi-model reasoning |
| `serena` | 3006 | mcp | `GET /health` | ADHD-optimized code intelligence |

### 11.3 Coordination Layer

| Service | Port | Category | Health | Role |
|---|---|---|---|---|
| `dopecon-bridge` | 3016 | coordination | `GET /health` | Central event hub, auth gateway, SSE stream |
| `leantime` | 8080 | coordination | `GET /` | PM application UI |
| `leantime-bridge` | 3015 | coordination | `GET /health` | Leantime ↔ MCP bridge |
| `webhook-receiver` | 8790 | coordination | `GET /healthz` | OpenAI webhook ingestion |

### 11.4 Cognitive Layer

| Service | Port(s) | Category | Health | Role |
|---|---|---|---|---|
| `adhd-engine` | 8095 (internal) → 3025 (external) | cognitive | `GET /health` | ADHD accommodations, energy tracking |
| `task-orchestrator` | 8000 (internal) → 3014 (external) | cognitive | `GET /health` | ADHD-aware task management, workflow API |

### 11.5 Dependency Graph

```
postgres ───────┬── conport
                ├── dopecon-bridge
                └── dope-memory

qdrant ─────────┬── conport
                ├── dope-context
                ├── dopecon-bridge
                └── leantime-bridge

redis-events ───┬── dopecon-bridge
                └── dope-memory

redis-primary ──┬── adhd-engine
                └── task-orchestrator

dopecon-bridge ─┬── task-orchestrator
                └── adhd-engine

conport ────────── task-orchestrator

leantime ───────── leantime-bridge
```

EVIDENCE: `services/registry.yaml#services`, `compose.yml`

---

## 12. Smoke Stack (Minimal Operational Set)

The smoke stack defines the minimum services required for system operation:

| Service | Port | Purpose |
|---|---|---|
| `conport-http` | 3004 | Knowledge graph |
| `dopecon-bridge` | 3016 | Event coordination |
| `dope-memory` | 3020 | Temporal chronicle |
| `postgres` | 5432 | Primary database |
| `qdrant` | 6333 | Vector search |
| `task-orchestrator` | 8000 | Task management |

EVIDENCE: `services/registry.yaml#enabled_in_smoke`

---

## 13. ConPort MCP Tool Surface

The ConPort MCP server provides the persistence backbone for all agent operations.

| Tool | Parameters | Purpose |
|---|---|---|
| `add_decision()` | `workspace_id, title, rationale, impl_details, tags, links` | Log architectural decision |
| `attach_artifact()` | `workspace_id, kind, title, path, hash, size_bytes` | Store file/diff artifacts |
| `get_decisions()` | `workspace_id, since, tags_filter, limit` | Query decision history |
| `graph_link()` | `workspace_id, source_type, source_id, rel_type, target_type, target_id` | Create knowledge graph edges |
| `semantic_search()` | `workspace_id, query, entity_types, limit` | Vector similarity search |
| `upcoming_add()` | `workspace_id, title, description, priority, due_date, tags` | Add work item |
| `work_update_status()` | `workspace_id, work_item_id, status` | Update work item state |

**Entity Types:** `ARTIFACT`, `DECISION`, `WORK_ITEM`

**Relationship Types:** `ATTACHED_TO`, `CREATED_BY`, `DEPENDS_ON`, `IMPLEMENTS`, `REFERENCES`, `VALIDATES`

EVIDENCE: `src/dopemux/mcp/conport_mcp_tools.py#ConPortMCPTools` (L125-200)

---

## 14. Disconnected Flows

The following architectural elements are defined but not fully connected:

| Component | Status | Evidence |
|---|---|---|
| `file-watch` hook | Defined but handler not implemented | `src/dopemux/hooks/hook_manager.py` — marked experimental |
| `git-commit` internal hook | Defined but disabled by default | `src/dopemux/hooks/hook_manager.py` — `enabled=False` |
| `CUSTOM` agent type | Enum value exists, no static implementation | `src/dopemux/agent_orchestrator.py` — dynamic registration only |
| Fish shell hooks | Shell type detected but hook generation not implemented | `src/dopemux/hooks/shell_hook_installer.py` — bash/zsh only |
| Cursor editor | No integration surface found | No `.cursor/` directory in repository |
| VS Code editor | No integration surface found | No `.vscode/` directory in repository |
| EditorConfig | No configuration found | No `.editorconfig` file in repository |

---

## 15. Cross-Cutting Concerns

### 15.1 ADHD Safety Invariants

All agent flows enforce ADHD-safe patterns:

- **Break enforcement:** CognitiveGuardian enforces 25-min Pomodoro intervals and 90-min mandatory breaks
- **Context preservation:** MemoryAgent auto-saves every 30 seconds; MCP Broker checkpoints on role switch (<200ms)
- **Energy gating:** Claude Code `check_energy.sh` blocks complex tools when `energy=low`
- **Error isolation:** All hooks are non-blocking with timeout enforcement (50–500ms)
- **Progressive disclosure:** Top-k rules enforced on tool outputs; results trimmed by MCP pre-tool hooks

### 15.2 Workspace Isolation

All state is scoped by `workspace_id` and `instance_id`:

- ConPort knowledge graph entries are workspace-scoped
- MCP proxy routes workspace parameters to workspace-aware servers
- MemoryAgent sessions are instance-scoped
- EventBus subscriptions are process-local (InMemory) or namespace-scoped (Redis Streams)

### 15.3 Determinism Guarantees

- Agent dispatch is priority-deterministic (lowest priority value wins ties)
- MCP Broker startup follows a fixed Phase 0 → Phase 5 sequence with a mandatory DiscoveryGate
- Hook execution order is registration-order within the HookManager
- Event pattern matching follows exact → prefix → wildcard precedence
