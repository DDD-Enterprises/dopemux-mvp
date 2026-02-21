# Dopemux inventory (from UPGRADES run outputs)

- Generated: 2026-02-20 10:37:18Z
- Run id: `docs_substrate_20260217_142101_15718`
- Run root: `/Users/hue/code/dopemux-mvp/extraction/runs/docs_substrate_20260217_142101_15718`

## 1) Extraction phase status (norm artifacts present in this run)

- A_repo_control_plane: OK (14 files)
- H_home_control_plane: OK (13 files)
- D_docs_pipeline: OK (248 files)
- C_code_surfaces: OK (19 files)
- E_execution_plane: OK (11 files)
- W_workflow_plane: OK (2 files)
- B_boundary_plane: OK (7 files)
- G_governance_plane: EMPTY (0 files)
- Q_quality_assurance: OK (2 files)
- R_arbitration: EMPTY (0 files)
- X_feature_index: EMPTY (0 files)
- T_task_packets: EMPTY (0 files)
- Z_handoff_freeze: EMPTY (0 files)

## 2) Systems

### 2.1 Documented system hubs (docs/systems/*)

- adhd-engine
- adhd-features
- adhd-intelligence
- agents
- conport
- conport-kg-ui
- dddpg
- dope-context
- dopecon-bridge
- gpt-researcher
- multi-workspace
- orchestrator
- production
- serena
- task-orchestrator

### 2.2 Boundary-plane component inventory (from BOUNDARY_INVENTORY.json)

- dopemux CLI - COMP-B01 / Interface
- DopeconBridge (port 3016) - COMP-B02 / Bridge
- Task Orchestrator (port 8095) - COMP-B03 / Orchestration
- DOPE Layout Engine - COMP-B04 / UI/UX
- LiteLLM Proxy (port 4000) - COMP-B05 / Gateway
- Profile Manager - COMP-B06 / Configuration
- Instance Slash Commands - COMP-B07 / Interface

## 3) Services

### 3.1 Canonical docker compose services (compose.yml)

- adhd-engine
- conport ports: 3004:3004, 4004:4004 container: mcp-conport
- desktop-commander ports: 3012:3012 container: dopemux-mcp-desktop-commander
- dope-context ports: 3010:3010 container: mcp-dope-context
- dope-memory ports: 8096:3020
- dopecon-bridge ports: 3016:3016 container: dope-decision-graph-bridge
- genetic-agent ports: 8000:8000 container: dopemux-genetic-agent
- gptr-mcp ports: 3009:3009 container: dopemux-mcp-gptr-mcp
- leantime ports: 8080:80 container: leantime
- leantime-bridge ports: 3015:3015 container: dopemux-mcp-leantime-bridge
- litellm ports: 4000:4000 container: mcp-litellm
- mcp-qdrant ports: 6333:6333, 6334:6334 container: mcp-qdrant
- mysql_leantime container: mysql_leantime
- pal ports: 3003:3003 container: mcp-pal
- postgres ports: 5432:5432 container: dopemux-postgres-age
- redis-events ports: 6379:6379 container: redis-events
- redis-primary container: redis-primary
- redis-ui ports: 8081:5540 container: dopemux-redis-ui
- redis_leantime container: redis_leantime
- serena ports: 3006:3006, 4006:4006 container: dopemux-mcp-serena
- task-orchestrator

### 3.2 Service registry entries (services/registry.yaml)

- activity-capture (port 8096, sensory) - Activity Capture - Passive development activity tracking and logging
- adhd-dashboard (port 8097, cognitive) - ADHD Dashboard - Specific visualization of energy, attention, and cognitive load
- adhd-engine (port 8095, cognitive) - ADHD Engine (Serena) - Real-time ADHD accommodation service
- adhd-notifier (port 8098, cognitive) - ADHD Notifier - Context-aware notification routing and break management
- desktop-commander (port 3012, mcp) - Desktop Commander MCP - desktop automation and window control
- dope-memory (port 3020, mcp) - Dope-Memory - Temporal chronicle and working-context manager
- dope-query (port 3004, mcp) - DopeQuery (ConPort runtime) - Knowledge graph and context management MCP server
- dopecon-bridge (port 3016, coordination) - DopeconBridge - Central coordination and event routing layer
- exa (port 3008, mcp) - Exa Search MCP - Neural semantic web search integration
- leantime (port 8080, coordination) - Leantime PM application container for strategic planning and ticket workflows
- leantime-bridge (port 3015, coordination) - Leantime Bridge MCP - project management integration over HTTP/SSE
- litellm (port 4000, infrastructure) - LiteLLM Proxy - Unified OpenAI-compatible interface for all LLM providers (GPT, Grok, Claude)
- plane-coordinator (port 8090, coordination) - Plane Coordinator - two-plane coordination API between PM and cognitive systems
- postgres (port 5432, infrastructure) - PostgreSQL database with AGE extension for knowledge graph
- qdrant (port 6333, infrastructure) - Qdrant vector database for semantic search
- redis (port 6379, infrastructure) - Redis for caching and event streaming
- task-orchestrator (port 8000, cognitive) - Task Orchestrator - ADHD-aware task coordination service
- voice-commands (port 3007, sensory) - Voice Commands - Voice-to-text task decomposition API
- workspace-watcher (port 8100, sensory) - Workspace Watcher - Real-time file system monitoring and change detection

### 3.3 Repo service directories (services/*)

- .claude
- activity-capture [registry exec]
- adhd-dashboard [registry]
- adhd-engine [compose registry exec]
- adhd-notifier [registry exec]
- adhd_engine
- agents
- claude_brain
- complexity_coordinator
- conport_kg_ui
- copilot_transcript_ingester
- dddpg
- dope-context [compose exec]
- dope-query [registry]
- dopecon-bridge [compose registry exec]
- dopemux-gpt-researcher
- genetic_agent
- intelligence
- mcp-capture
- mcp-client [exec]
- ml-predictions
- ml-risk-assessment
- monitoring
- monitoring-dashboard
- serena [compose]
- session-intelligence
- session-manager
- session_intelligence
- shared
- slack-integration
- task-orchestrator [compose registry exec]
- task-router
- taskmaster
- taskmaster-mcp-client
- voice-commands [registry]
- working-memory-assistant
- workspace-watcher [registry exec]

### 3.4 Services referenced in execution startup graph (EXEC_STARTUP_GRAPH.json)

- ImplementationCollector
- PMCollector
- PaneManager
- RefreshLoop
- Settings
- StateStore
- TransientManager
- activity-capture
- adhd-engine
- adhd-notifier
- artifact
- break-suggester
- claude-code-router
- compose_files
- conport
- conport-memory
- desktop-commander
- docker-services
- dope-context
- dopecon-bridge
- dopemux-postgres-age
- dopemux-redis-events
- dopemux-redis-primary
- dopemux-redis-ui
- edges
- exa
- generated_at
- genetic-agent
- gpt-researcher
- invocation_surfaces
- leantime-bridge
- litellm
- mcp-clear-thought
- mcp-client
- mcp-conport
- mcp-desktop-commander
- mcp-dope-context
- mcp-exa
- mcp-gptr-mcp
- mcp-leantime-bridge
- mcp-pal
- mcp-qdrant
- mcp-serena
- mcp-servers
- mcp-task-orchestrator
- mcp-zen
- milvus-standalone
- pal
- plane-coordinator
- postgres
- resources
- serena-v2
- services
- session-focus
- startup_sequence
- task-orchestrator
- unknowns
- warnings
- workspace-watcher
- zep

## 4) Feature surfaces

### 4.1 Runtime modes

- Dopemux runtime modes: dev, implementation, local, pm, prod, smoke
- Dashboard modes: implementation, pm

### 4.2 MCP servers (repo-defined, from REPO_MCP_SERVER_DEFS.json)

- conport (sse | http://localhost:3004/sse)
- desktop-commander (stdio | cmd: docker exec -i mcp-desktop-commander python /app/mcp_server.py)
- dope-context (sse | http://localhost:3010/mcp)
- exa (stdio | cmd: docker exec -i mcp-exa python /app/exa_server.py)
- gpt-researcher (stdio | cmd: docker exec -i mcp-gptr-mcp python /app/server.py)
- leantime-bridge (sse | http://localhost:3015/sse)
- pal (stdio | cmd: uv run --directory /Users/hue/code/dopemux-mvp/docker/mcp-servers/pal/pal-mcp-server python server.py)
- serena-v2 (sse | http://localhost:3006/sse)
- task-orchestrator (stdio | cmd: python3 /Users/hue/code/dopemux-mvp/services/task-orchestrator/task_orchestrator/app.py)

### 4.3 MCP servers (home-defined, from HOME_MCP_SURFACE.json)

- claude-context (npx -y @zilliz/claude-context-mcp@latest)
- context7 (npx -y context7-mcp)
- dope-context (bash services/dope-context/run_mcp.sh)
- exa (npx -y exa-mcp)
- leantime (npx -y leantime-mcp)
- mas-sequential-thinking (python [REDACTED_LONG_TOKEN].py)
- morphllm-fast-apply (npx -y morphllm-fast-apply-mcp)
- pal (uvx --from git+https://github.[REDACTED_LONG_TOKEN].git pal-mcp-server)
- zen (npx -y zen-mcp)

### 4.4 Repo hooks (from REPO_HOOKS_SURFACE.json)

- check_energy.sh
- log_progress.sh
- prompt_analyzer.py
- save_context.sh

### 4.5 Operator/automation surfaces (from EXEC_BOOTSTRAP_COMMANDS.json)

- Slash commands extracted from repo instruction surface:
  - /doc:pull
  - /dx:implement
- docker compose / docker-compose commands:
  - docker compose -p dopemux -f compose.yml down --remove-orphans
  - docker compose -p dopemux -f compose.yml up -d --remove-orphans --force-recreate
  - docker compose config
  - docker-compose -f docker-compose.master.yml up
  - docker-compose -f docker-compose.smoke.yml up
- compose up/down targets (scripts):
  - docker compose -f docker-compose.smoke.yml up -d --build
  - docker compose -p "$PROJECT" -f compose.yml down --remove-orphans
  - docker compose -p "$PROJECT" -f compose.yml up -d --remove-orphans --force-recreate
  - docker-compose --profile manual up -d task-orchestrator
  - docker-compose -f "$ROOT_DIR/docker-compose.master.yml" up -d dopemux-postgres-age dopemux-redis-primary dopemux-redis-events mcp-qdrant
  - docker-compose -f "$ROOT_DIR/docker-compose.master.yml" up -d mcp-conport mcp-zen mcp-pal mcp-serena mcp-dope-context mcp-exa mcp-gptr-mcp mcp-leantime-bridge mcp-desktop-commander mcp-task-orchestrator mcp-clear-thought
  - docker-compose -f "$ROOT_DIR/docker/conport-kg/docker-compose.yml" up -d
  - docker-compose -f "$ROOT_DIR/docker/docker-compose.event-bus.yml" up -d
  - docker-compose -f "$ROOT_DIR/docker/leantime/docker-compose.yml" up -d
  - docker-compose -f "$ROOT_DIR/docker/memory-stack/docker-compose.yml" up -d
  - docker-compose -f docker-compose.age.yml down postgres-age
  - docker-compose -f docker-compose.age.yml up -d postgres-age
  - docker-compose -f docker-compose.master.yml up -d
  - docker-compose -f docker-compose.unified.yml up -d
  - docker-compose up -d
  - docker-compose up -d dopecon-bridge
- make targets:
  - attach
  - attach-minimal
  - build
  - clean
  - dashboard
  - docs
  - docs-audit
  - docs-audit-apply-rename
  - docs-audit-frontmatter-apply
  - help
  - install
  - install-dev
  - kill-minimal
  - kill-orchestrator
  - list-sessions
  - minimal
  - orchestrator
  - pm-down
  - pm-install
  - pm-install-unattended
  - pm-logs
  - pm-up
  - probe
  - probe-c
  - serve-docs
  - test
  - test-coverage
  - test-fast
  - test-integration
  - test-unit
  - test-verbose
  - x-doctor
  - x-manifest
  - x-phase-dirs
  - x-run-init
  - x-status
- npm scripts / npm global installs:
  - build
  - dev
  - lint
  - npm install -g @zilliz/claude-context-mcp@latest
  - npm install -g exa-mcp
  - npm install -g leantime-mcp
  - npm install -g morphllm-fast-apply-mcp
  - npm install -g typescript
  - npm install -g zen-mcp
  - npm list -g
  - start
- python entrypoints:
  - claude
  - dopemux --version
  - dopemux decisions --help
  - dopemux health
  - dopemux init
  - dopemux profile list
  - dopemux start
  - make format
  - make lint
  - make quality
  - make type-check
  - pip install -e .
  - pip install -e .[dev]
  - pytest --cov=src/dopemux --cov-report=term-missing
  - pytest tests/
  - pytest tests/ -m "not slow"
  - pytest tests/ -m integration
  - pytest tests/ -m unit
  - pytest tests/specific_test.py
  - pytest tests/specific_test.py::test_name
  - python -c "from storage import SQLiteBackend; print('OK DDDPG imports work')"
  - python main.py
  - python main.py --interval 5
  - python main.py --interval 60
  - python mcp_event_wrapper.py --server conport --instance A
  - python scripts/collect_task_packet.py
  - python scripts/compose_guard.py
  - python scripts/docs_frontmatter_guard.py --fix
  - python scripts/docs_normalize.py --apply
  - python scripts/docs_validator.py
  - python scripts/indexing/index_conport_in_dope_context.py
  - python scripts/pipeline_doctor.py
  - python scripts/pipeline_manifest.py
  - python scripts/ui/neon_dashboard/core/app.py
  - python scripts/utilities/adr_cleanup.py
  - python scripts/utilities/claude_code_event_integration.py
  - python scripts/utilities/emit-commit-event.py
  - python scripts/utilities/fix_mcp_config.py
  - python scripts/utilities/rfc_new.py "Title" [feature_id]
  - python scripts/utilities/serena_enrichment.py
  - python start_service.py hue
  - python tools/smoke_runtime_gate.py
  - python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
  - python3 -m dopemux.cli tmux start --layout dope
  - python3 -m mcp_service_info
  - python3 -m pip install -e .
  - python3 -m pytest
  - python3 UPGRADES/run_probe.py --phase "<PHASE>"
  - python3 scripts/create_phase3_leantime_tasks.py
  - python3 scripts/deploy/migration/generate_age_sql.py
  - python3 scripts/deploy/migration/import_to_postgresql_age.py --json-path /Users/hue/code/dopemux-mvp/scripts/migration/conport_export.json --db-url postgresql://dopemux_age:dopemux_age_dev_password@localhost:5456/dopemux_knowledge_graph
  - python3 scripts/deploy/migration/load_age_direct.py
  - python3 scripts/deploy/migration/load_age_edges.py
  - python3 scripts/deploy/migration/load_age_nodes.py
  - python3 scripts/deploy/migration/migrate.py --dry-run
  - python3 scripts/deploy/migration/migrate.py --full
  - python3 scripts/deploy/migration/migrate.py --phase1
  - python3 scripts/deploy/migration/migrate.py --phase2
  - python3 scripts/deploy/migration/reingest.py
  - python3 scripts/deploy/migration/rollback.py
  - python3 scripts/deploy/migration/switchover.py
  - python3 scripts/deploy/migration/validate.py
  - python3 scripts/deploy/migration/validate_age_pg_compat_stress.py
  - python3 scripts/dev/benchmarks/adhd_performance_baseline.py
  - python3 scripts/dev/benchmarks/performance_validation.py
  - python3 scripts/dopemux-compact-dashboard.py show
  - python3 scripts/dopemux-compact-dashboard.py show --mode all
  - python3 scripts/dopemux-dashboard.py launch --pane system
  - python3 scripts/mcp/wire_claude_mcp.py
  - python3 scripts/memory/test-memory-system.py
  - python3 scripts/wire_conport_project.py
  - python3 ~/code/dopemux-mvp/services/adhd_engine/cli/adhd.py break
  - python3 ~/code/dopemux-mvp/services/adhd_engine/cli/adhd.py check
  - python3 ~/code/dopemux-mvp/services/adhd_engine/cli/adhd.py status
- tmux wrappers / commands:
  - ./scripts/launch-adhd-dashboard.sh
  - ./scripts/launch-dopemux-minimal.sh
  - ./scripts/launch-dopemux-orchestrator.sh
  - dopemux wire-conport --instance "$INSTANCE_ID" --project "$REPO_ROOT"
  - python3 -m dopemux.cli tmux start --layout dope
  - tmux attach -t dmx
  - tmux attach -t dopemux-orchestrator
  - tmux attach-session -t $SESSION
  - tmux attach-session -t $SESSION_NAME
  - tmux kill-session -t dmx
  - tmux kill-session -t dopemux-orchestrator
  - tmux list-sessions
  - tmux new-session -d -s $SESSION -n main
  - tmux new-session -d -s $SESSION_NAME -n "Orchestrator" -c $WORKSPACE
  - tmux select-pane -t $SESSION:0.0 -T "Dashboard"
  - tmux select-pane -t $SESSION:0.1
  - tmux select-pane -t $SESSION:0.1 -T "CLI"
  - tmux select-pane -t $SESSION_NAME:0.0
  - tmux select-pane -t $SESSION_NAME:0.0 -T "ADHD Dashboard"
  - tmux select-pane -t $SESSION_NAME:0.1
  - tmux select-pane -t $SESSION_NAME:0.1 -T "Dopemux CLI"
  - tmux select-pane -t $SESSION_NAME:0.2 -T "Service Logs"
  - tmux select-pane -t $SESSION_NAME:0.3 -T "Monitoring"
  - tmux select-pane -t 0
  - tmux select-pane -t 1
  - tmux send-keys
  - tmux send-keys -t $SESSION:0.0 "python3 scripts/dopemux-compact-dashboard.py show" C-m
  - tmux send-keys -t $SESSION:0.1 "echo 'Dopemux CLI Ready'; echo 'Run: docker-compose up -d'" C-m
  - tmux send-keys -t $SESSION_NAME:0.0 "cd $WORKSPACE" C-m
  - tmux send-keys -t $SESSION_NAME:0.0 "python3 scripts/dopemux-compact-dashboard.py show --mode all" C-m
  - tmux send-keys -t $SESSION_NAME:0.1 "cd $WORKSPACE" C-m
  - tmux send-keys -t $SESSION_NAME:0.1 "clear" C-m
  - tmux send-keys -t $SESSION_NAME:0.2 "cd $WORKSPACE" C-m
  - tmux send-keys -t $SESSION_NAME:0.2 "echo 'Service Logs - Waiting for services to start...'" C-m
  - tmux send-keys -t $SESSION_NAME:0.3 "cd $WORKSPACE" C-m
  - tmux set-option -t $SESSION pane-border-status top
  - tmux set-option -t $SESSION_NAME pane-border-format "#{pane_index}: #{pane_title}"
  - tmux set-option -t $SESSION_NAME pane-border-status top
  - tmux source-file
  - tmux source-file ~/.tmux.conf
  - tmux split-window -h -p 50 -t $SESSION_NAME:0.2
  - tmux split-window -h -p 67 -t $SESSION_NAME:0.1
  - tmux split-window -v -p 20 -t
  - tmux split-window -v -p 80 -t $SESSION:0
  - tmux split-window -v -p 80 -t $SESSION_NAME:0

### 4.6 Dashboard/API surface (from API_DASHBOARD_SURFACE.json)

- GET / - Root endpoint returning service info
- PUT /api/v1/activity/{user_id} - Log user activity event for ADHD tracking
- POST /api/v1/assess-task - Assess task suitability for user's current ADHD state
- GET /api/v1/attention-state/{user_id} - Get current attention state for user
- POST /api/v1/automation-level/{user_id} - Adjust automation level for prediction type
- POST /api/v1/break-recommendation - Get intelligent break recommendation based on current ADHD state
- GET /api/v1/breaks/{user_id} - Get break timing information for user
- POST /api/v1/code-complexity - Get code complexity assessment
- GET /api/v1/cognitive-load/{user_id} - Get current cognitive load for user
- GET /api/v1/customization-settings/{user_id} - Get user customization settings
- POST /api/v1/customization-settings/{user_id} - Update user customization settings for ADHD Engine
- GET /api/v1/energy-level/{user_id} - Get current energy level for user
- GET /api/v1/external-activity - Get external activity metrics from Desktop Commander and Calendar
- GET /api/v1/flow-state/{user_id} - Get current flow state for user
- POST /api/v1/log-git-event - Log git event from git hooks
- POST /api/v1/log-intent - Log user intent from Claude Code prompt analysis
- GET /api/v1/metrics - Prometheus metrics endpoint for performance monitoring
- POST /api/v1/override-prediction - Allow user to override an ML prediction
- GET /api/v1/patterns/{user_id} - Retrieve learned ADHD patterns for user
- POST /api/v1/predict - Get ML prediction for energy, attention, or break timing
- POST /api/v1/prediction-feedback/{user_id} - Submit feedback on prediction usefulness
- POST /api/v1/recommend-break - Get personalized break recommendation
- POST /api/v1/record-progress - Record progress from Claude Code PostToolUse hook
- POST /api/v1/save-context - Save current context from Claude Code hooks
- GET /api/v1/session-time/{user_id} - Get current session duration for user
- GET /api/v1/state - Get current ADHD state for Claude Code hooks
- GET /api/v1/statusline/{user_id} - Statusline data endpoint for Claude Code integration
- GET /api/v1/tasks - Get task completion metrics for dashboard
- GET /api/v1/trust-metrics/{user_id} - Get trust metrics for user
- GET /api/v1/trust-visualization/{user_id} - Get trust visualization data
- GET /api/v1/unfinished-work - Get count and list of unfinished work items
- POST /api/v1/user-profile - Create or update user ADHD profile
- WEBSOCKET /api/v1/ws/stream - Real-time event streaming to dashboard via WebSocket
- POST /auth/refresh - Refresh access token
- POST /auth/token - Authenticate and return access token
- GET /conport/active_context - Get current active context from ConPort
- GET /conport/custom_data - Retrieve custom data from ConPort with circuit breaker fallback
- POST /conport/custom_data - Save custom data to ConPort with circuit breaker fallback
- POST /conport/decision - Log architectural decision to ConPort
- POST /conport/semantic_search - Perform semantic search across ConPort data
- GET /coordination/conflicts - Resolve coordination conflicts
- GET /coordination/status - Get overall team coordination status
- GET /ddg/decisions - Get recent decisions from the decision graph
- GET /ddg/search - Search decisions by text query
- POST /dependencies - Register a new external dependency
- GET /dependencies/status - Get status of critical external dependencies
- GET /dependencies/{id}/alternatives - Suggest alternatives when dependency fails
- GET /dependencies/{id}/health - Perform health check on specific dependency
- GET /dopemux/api/attention-state - Get current attention state
- POST /dopemux/api/attention-state - Update attention state
- POST /dopemux/api/break-reminder - Set break reminder
- GET /dopemux/api/cognitive-load - Get current cognitive load
- POST /dopemux/api/cognitive-load - Update cognitive load
- GET /dopemux/api/context - Restore context
- POST /dopemux/api/context - Save context
- GET /epics - List workflow epics with optional filters
- POST /epics - Create a new workflow epic
- PATCH /epics/{id} - Update an existing workflow epic
- POST /events - Publish event to Redis Stream for cross-service coordination
- GET /events/history - Get event history from Redis Stream
- POST /events/progress-updated - Publish progress_updated event (convenience endpoint)
- POST /events/session-started - Publish session_started event (convenience endpoint)
- GET /events/stream - Subscribe to event stream via Server-Sent Events (SSE)
- POST /events/tasks-imported - Publish tasks_imported event (convenience endpoint)
- GET /health - Basic heartbeat + persona metadata
- GET /ideas - List workflow ideas with optional filters
- POST /ideas - Create a new workflow idea
- PATCH /ideas/{id} - Update an existing workflow idea
- POST /ideas/{id}/promote - Promote an idea to an epic
- GET /kg/custom_data - Retrieve custom data from ConPort
- POST /kg/custom_data - Save custom data to ConPort (for orchestrator checkpoints)
- POST /kg/decisions - Create a decision in ConPort via MCP
- GET /kg/decisions/recent - Get recent decisions (Tier 1)
- GET /kg/decisions/search - Search decisions by tag or full-text
- GET /kg/decisions/{decision_id}/context - Get complete decision context (Tier 3)
- GET /kg/decisions/{decision_id}/neighborhood - Get decision neighborhood with progressive disclosure (Tier 2)
- GET /kg/decisions/{decision_id}/summary - Get decision summary with relationship count (Tier 1)
- GET /kg/health - Health check endpoint
- POST /kg/links - Create a link between ConPort items via MCP
- GET /kg/progress - Get progress entries from ConPort
- POST /kg/progress - Create a progress entry in ConPort via MCP
- GET /presets - Lists available spice/register combos
- POST /research/create - Create a new research task with ADHD optimizations
- POST /research/{task_id}/complete - Mark research task as complete and finalize results
- POST /research/{task_id}/execute/{question_index} - Execute a single research question with pause capability
- POST /research/{task_id}/pause - Pause research task for ADHD context switching
- POST /research/{task_id}/plan - Generate research plan for transparent ADHD workflow
- POST /research/{task_id}/resume - Resume paused research task
- GET /research/{task_id}/status - Get current status and progress of research task
- POST /risk/assess - Assess risk for an entity
- GET /risk/blockers - Predict potential blockers
- POST /risk/feedback - Update prediction feedback
- GET /risk/mitigations - Generate mitigation strategies
- POST /roast - Generates 1-10 roast lines
- POST /route/cognitive
- POST /route/pm
- GET /tasks - List tasks from the task-orchestrator
- POST /tasks - Store a task
- POST /tasks/coordinate - Coordinate task execution
- GET /tasks/next/{project_id} - Get next actionable tasks for ADHD-friendly workflow
- POST /tasks/parse-prd - Parse PRD document into tasks across all systems with ADHD context preservation
- POST /tasks/schedule - Schedule subtasks
- GET /tasks/{id} - Retrieve task by ID
- POST /tasks/{id}/breakdown - Break down complex task
- GET /tasks/{task_id} - Retrieve a specific task by ID
- PUT /tasks/{task_id} - Update an existing task
- PATCH /tasks/{task_id}/status - Update task status across all systems
- POST /teams - Register a new team for coordination
- GET /teams/{id}/optimize - Optimize workload for a specific team
- WEBSOCKET /ws/progress/{user_id} - WebSocket endpoint for real-time progress updates

### 4.7 Event bus surface (from EVENTBUS_SURFACE.json)

- Named events:
  - tickets.created
  - tickets.updated
  - user.login
- Event types:
  - break.taken
  - code.complexity.high
  - cognitive.state.change
  - context.switch.detected
  - decomposition.completed
  - pm.decision.linked
  - pm.sync.failed
  - pm.sync.requested
  - pm.sync.succeeded
  - pm.task.blocked
  - pm.task.completed
  - pm.task.created
  - pm.task.status_changed
  - pm.task.updated
  - session.start
  - shield.focus.ended
  - shield.focus.started
  - shield.interruption.detected
  - task.created
  - task.updated
- Channels:
  - console
  - dashboard
  - push
  - tmux_popup
  - tmux_status
  - voice
- Streams:
  - activity.events.v1
  - dopemux:events
  - memory.derived.v1
- Consumer groups:
  - adhd-notifier-breaks

### 4.8 Dope-Memory surface (from DOPE_MEMORY_CODE_SURFACE.json)

- context_save (DopemuxController.php:saveContext) - Save user context data
- context_restore (DopemuxController.php:restoreContext) - Restore user context data
- context_snapshot_save (ContextSnapshot.php:saveSnapshot) - Save context snapshot to database
- context_snapshot_get (ContextSnapshot.php:getSnapshot) - Retrieve context snapshot from database

### 4.9 Profiles (from HOME_PROFILES_SURFACE.json)

- act
- adhd-default
- architect
- dangerous
- developer
- minimal
- plan
- python-ml
- quickfix
- researcher
- safe
- web-dev

### 4.10 Workflows (from WORKFLOW_INVENTORY.json)

- Count: 367

| workflow_id | name | source_file |
| --- | --- | --- |
|  | ADHD Optimization Workflow |  |
|  | ADHD-Optimized Daily Session | SESSION_PLAN_WEEK1_DAY2.md |
|  | ADHD-Optimized Environment Setup |  |
|  | Agent Implementation Workflow | complete-16-week-plan-summary.md |
|  | Agent Role & Persona Switching |  |
|  | Daily Task Management Workflow | conport-tracking-guide.md |
|  | Extraction Doctor & Reprocessing |  |
|  | Foundation Analysis Workflow |  |
|  | Interrupt Recovery Workflow |  |
|  | Knowledge Graph Management Workflow |  |
|  | MCP Startup and Validation Workflow | IMPLEMENTATION_COMPLETE.md |
|  | Multi-Instance Management Workflow |  |
|  | Multi-Session & Git Worktree Management |  |
|  | Platform Compatibility Testing | SESSION_PLAN_WEEK1_DAY2.md |
|  | Rapid Service Rollout Workflow | RAPID_ROLLOUT_SESSION.md |
|  | Release and Packaging Workflow | QUICK_REFERENCE_DAY4.md |
|  | Serena V2 Production Deployment |  |
|  | Systematic Code Review Workflow |  |
|  | Task Orchestration Workflow |  |
|  | Testing and Validation Workflow |  |
|  | Troubleshooting & System Diagnostics |  |
|  | Untracked Work Detection & Management |  |
| ADHD_TASK_ORCHESTRATION | ADHD-Aware Task Orchestration |  |
| ADR-197_4_STAGE_WORKFLOW | 4-Stage Task Workflow |  |
| BLUESKY_DEVELOPMENT_WORKFLOW | Bluesky Feature Development |  |
| BUG_REPAIR_WORKFLOW | Standard Bug Repair |  |
| COGNITIVE_STATE_MONITORING | Real-time Cognitive Monitoring |  |
| F-NEW-7_PHASE_1_MIGRATION | Multi-Tenancy Migration |  |
| F-NEW-7_PHASE_2_UNIFIED_QUERY | Unified Query Layer |  |
| F-NEW-7_PHASE_3_INTELLIGENCE | Cross-Agent Intelligence |  |
| F-NEW-8_INTEGRATION | Break Suggester Integration |  |
| KNOWLEDGE_GRAPH_COORDINATION | ConPort-KG Memory Coordination |  |
| MOBILE_NOTIFICATION_FLOW | Mobile Push Notification Workflow |  |
| SERVICE_HEALTH_MONITORING | Unified Service Health Monitoring |  |
| W1_CONTEXT_CAPTURE | Context Capture & Snapshotting |  |
| W2_PREDICTIVE_RESTORATION | Predictive Context Restoration |  |
| W3_DOPE_MEMORY_INGESTION | Dope-Memory Event Processing & Storage |  |
| W4_REFLECTION_TRAJECTORY | Reflection & Trajectory Analysis |  |
| W5_VALIDATION_TESTING | Performance Validation & Service Testing |  |
| WF-ACTIVITY-CAPTURE | Automated Activity Tracking |  |
| WF-ADHD-001 | ADHD Activity Tracking | adhd-stack-readme.md |
| WF-ADHD-STATE-MONITORING | Real-time Cognitive State Assessment |  |
| WF-AUD-001 | Server Audit & Maintenance | SERVER_AUDIT_2026-02-05.md |
| WF-AUDIT-001 | Optimized Code Audit |  |
| WF-BREAK-MANAGEMENT | Intelligent Break & Hyperfocus Protection |  |
| WF-DAILY-REPORTING | Cognitive Pattern Reporting |  |
| WF-DASH-001 | ADHD-Optimized Dashboard Display |  |
| WF-DEBT-001 | Genetic Agent Nesting Investigation |  |
| WF-ENV-001 | Service Environment Standardization | service-env-contract.md |
| WF-EXEC-002 | Infrastructure Agent Coordination |  |
| WF-FEATURE-001 | Comprehensive Feature Status Summary |  |
| WF-INC-001 | Security Incident Response | security.md |
| WF-MAINT-006 | System Integration & Setup |  |
| WF-MCP-001 | MCP Response Budget Verification |  |
| WF-MEM-004 | Working Memory Snapshot & Recovery |  |
| WF-MON-001 | Unified Health Monitoring | monitoring-dashboard.md |
| WF-NAV-001 | ADHD-Optimized Navigation | serena-v2-mcp-tools.md |
| WF-NAV-002 | Decision Reduction Workflow | serena-v2-mcp-tools.md |
| WF-NAV-003 | Complexity-Aware Reading | serena-v2-mcp-tools.md |
| WF-OPT-001 | Performance Optimization Workflow | PERFORMANCE_BASELINE.md |
| WF-ORCH-003 | Tactical Task Orchestration |  |
| WF-PM-001 | Idea-to-Epic Promotion | task-orchestrator.md |
| WF-PROFILE-001 | Profile System Verification |  |
| WF-ROUT-005 | Energy-Aware Task Routing |  |
| WF-SEARCH-001 | Semantic Search Reference Inventory |  |
| WF-SEC-001 | Security Implementation Workflow | security.md |
| WF-STABILITY-001 | Runtime Stability Hotfix Verification |  |
| WF-TASK-RECOMMENDATION | ADHD-Aware Task Selection |  |
| WF-UI-001 | Dashboard Enhancement Workflow | dashboard-enhancements.md |
| WF_CODE_SURFACE | Code Surface Analysis |  |
| WF_CONPORT_INTEGRATION | ConPort Knowledge Graph Integration |  |
| WF_DOC_PIPELINE | Phased Documentation Extraction |  |
| WF_HOME_CONFIG | Home Configuration Extraction |  |
| WF_INSTRUCTION_PLANE | LLM Instruction Plane Indexing |  |
| WF_OPS_WORKFLOW | Ops Workflow Extraction |  |
| WF_PROGRESSIVE_DISCLOSURE | Progressive Disclosure Orchestration |  |
| WF_REALTIME_RELEVANCE_SCORING | Real-time Relationship Relevance Scoring |  |
| WF_SYNTHESIS | Architecture Synthesis & Migration |  |
| WF_THRESHOLD_COORDINATION | Personalized Threshold Coordination |  |
| ZEN_ENHANCED_TIER_3 | Zen-Enhanced Advanced Features |  |
| activity_aggregation | Activity Capture & Aggregation |  |
| activity_tracking | User Activity Analysis |  |
| adhd-engine-assessment | ADHD Cognitive Assessment |  |
| adhd_accommodation_loop | ADHD Accommodation & Monitoring |  |
| adhd_aware_event_coordination |  |  |
| adhd_break_tracking | ADHD-Optimized Break Management |  |
| adhd_context_preservation | ADHD Context Preservation (ConPort) |  |
| adhd_engine_lifecycle | ADHD Engine Feature Development |  |
| adhd_feature_engagement | ADHD Feature Engagement | 02-how-to/adhd-features-user-guide.md |
| adhd_focus_window_management | Focus Window Management | docs/planes/pm/dopemux/05_ADHD_EXECUTION_MODEL.md |
| adhd_intelligence_stack | ADHD Intelligence Stack Deployment |  |
| adhd_optimized_query_execution | ADHD-Optimized Query Execution |  |
| adhd_performance_alerting | ADHD-Critical Metrics Pipeline |  |
| adhd_profile_adaptation | ADHD Profile Detection and Adaptation |  |
| adhd_ux_feedback |  |  |
| agent_event_propagation |  |  |
| architectural_hardening_loop | Architectural Hardening Loop |  |
| architecture_3_phase_1_audit | Architecture 3.0 Phase 1: Dependency Audit |  |
| architecture_decision |  |  |
| attention_aware_search |  |  |
| automated_pattern_detection | Automated Pattern Detection |  |
| autonomous_indexing |  |  |
| autonomous_indexing | Autonomous Background Indexing |  |
| batch_quality_optimization | Batch Quality Optimization |  |
| batch_work_tracking | Batch Auto-Track Processing |  |
| break_orchestration | Break Orchestration & Guidance |  |
| break_suggestion | Proactive Break Suggestion |  |
| bug_investigation |  |  |
| chatlog_synthesis | Chatlog Extraction Pipeline |  |
| chronicle_capture_pipeline | Chronicle Capture Pipeline |  |
| chronicle_mirroring | SQLite to Postgres Mirroring |  |
| claude_code_integration | Claude Code Integration Strategy |  |
| claude_code_integration | Claude Code Tools Integration |  |
| claude_launch_optimized | Optimized Claude Code Launch |  |
| claude_orchestrator_workflow | Claude Orchestrator Workflow |  |
| claude_project_init | Claude Project Initialization |  |
| code_audit_remediation | System-Wide Code Audit and Remediation | overview-audit-complete.md |
| code_indexing_pipeline |  |  |
| code_structural_indexing | Code Structural Indexing & Graph Storage |  |
| cognitive_guard_monitoring | Cognitive Guard Monitoring Loop |  |
| cognitive_guarding | CognitiveGuardian Monitoring |  |
| cognitive_load_management | Cognitive Load Balancing |  |
| cognitive_load_prediction | Real-time Cognitive Load Prediction |  |
| cognitive_pattern_detection |  |  |
| cognitive_state_sync | Cognitive State Synchronization |  |
| cognitive_support_loop | ADHD Proactive Cognitive Support |  |
| cognitive_task_routing |  |  |
| command_parsing_and_routing |  |  |
| command_safety_interception | Command Safety Interception |  |
| commit_tracking | Git Commit Event Emission |  |
| compact_dashboard_setup | Compact ADHD Dashboard Setup | COMPACT-DASHBOARD-COMPLETE.md |
| complexity_gating | Complexity Gating | docs/planes/pm/dopemux/05_ADHD_EXECUTION_MODEL.md |
| complexity_scoring | Unified Complexity Scoring |  |
| conport_data_contract_adapters | Component 2: Data Contract Adapters |  |
| conport_data_persistence | ConPort Data Persistence |  |
| conport_path_c_deployment | ConPort Event Bridge Deployment (Path C) | CONPORT_PRODUCTION_DEPLOYMENT_COMPLETE.md |
| consensus_validation |  |  |
| context_auto_save | MemoryAgent Context Auto-Save |  |
| context_checkpointing |  |  |
| context_preservation | Context Preservation |  |
| context_preservation_workflow | Context Preservation and Restoration |  |
| context_switch_tracking | Context Switch Analysis |  |
| contextual_ide_enrichment | Context-Aware IDE Hover Enrichment |  |
| cross_agent_intelligence | Cross-Agent Intelligence Correlation |  |
| cross_plane_coordination | Cross-Plane Bridge Operations |  |
| cross_plane_task_sync | Cross-Plane Task Synchronization |  |
| cross_session_persistence_sync | Cross-Session Persistence Synchronization |  |
| daily_sync | Incremental Workspace Sync |  |
| dashboard_implementation | Metrics Dashboard Implementation |  |
| dashboard_refresh | Dashboard Refresh Loop |  |
| decision_graph_exploration | Dope Decision Graph (DDG) Querying |  |
| deep_research | Deep Research (PACKET DR-1) |  |
| deployment_pipeline_orchestration | Deployment Pipeline Orchestration |  |
| design_first_governance | Design-First Prompting & Complexity Detection |  |
| deterministic_promotion | Deterministic Event Promotion |  |
| developer_pattern_learning | Developer Behavior Modeling & Personalization |  |
| development_release | Zen Commit and Release Pipeline |  |
| doc_gate | Doc Gate Verification |  |
| doc_standardization | Documentation Standardization |  |
| docker_cleanup | Docker Environment Cleanup | DOCKER_CLEANUP_PLAN.md |
| docs_indexing_pipeline |  |  |
| document_ingestion |  |  |
| document_intelligence_pipeline | Document Intelligence Pipeline |  |
| documentation_consolidation | Documentation Deduplication and Consolidation |  |
| dope_context_fix | Dope-Context Tool Fix | DOPE_CONTEXT_FIX_SUMMARY.md |
| dopecon_bridge_completion | DopeconBridge Completion and Migration |  |
| dopecon_bridge_event_pipeline | DopeconBridge Event Pipeline |  |
| dopeconbridge_migration | DopeconBridge Migration Workflow | DOPECONBRIDGE_QUICK_START_OLD.md |
| dopeconbridge_migration | DopeconBridge Migration and Expansion |  |
| dopeconbridge_wiring | Component 3: DopeconBridge Wiring |  |
| dopeconbridge_zen_integration | DopeconBridge Zen Integration Master Plan | DOPECONBRIDGE_ZEN_INTEGRATION_PLAN.md |
| dopemux_enhancement_rollout | Dopemux Enhancement Deployment | DOPEMUX_ENHANCEMENT_DEPLOYMENT.md |
| effectiveness_evolution_cycle | Effectiveness-Based Evolution Cycle |  |
| energy_adaptive_ui | Energy-Adaptive UI Management |  |
| energy_trend_analysis | Energy Rhythm Tracking |  |
| enhanced_genetic_repair | Enhanced Genetic Repair |  |
| env_contract_compliance | Unified Service Environment Contract Compliance |  |
| event_coordination | Async Event Coordination |  |
| event_driven_coordination | Event-Driven Coordination |  |
| event_ingestion_governance | Event Ingestion Governance |  |
| event_ingestion_promotion | Event Ingestion and Promotion |  |
| event_ingestion_redaction | Event Ingestion and Redaction |  |
| event_promotion | Dope-Memory Event Promotion |  |
| event_suppression_coordination | Event Suppression & Coordination |  |
| external_activity_monitoring | External Activity Monitoring |  |
| external_integrations |  |  |
| external_system_sync |  |  |
| fatigue_mode_protection | Fatigue Mode Protection | docs/planes/pm/dopemux/05_ADHD_EXECUTION_MODEL.md |
| feature_implementation |  |  |
| federated_personalization | Privacy-Preserving Federated Personalization |  |
| file_activity_monitoring | File Activity Monitoring |  |
| full_pipeline_upgrades | Full Pipeline Upgrades |  |
| gpt_researcher_deep_research | GPT-Researcher Deep Research |  |
| hardcoded_paths_migration | Hardcoded Paths Migration | HARDCODED_PATHS_AUDIT.md |
| hello_flow | Dopemux Hello-Flow |  |
| hybrid_search |  |  |
| hybrid_search_retrieval | Hybrid Search & Retrieval |  |
| ide_workflow_hooks | IDE Workflow Hooks |  |
| idea_to_epic_lifecycle | Stage-1 to Stage-2 Workflow Promotion |  |
| implementation_session |  |  |
| implicit_adhd_detection | Implicit ADHD Detection |  |
| initial_setup | Initial Workspace Indexing |  |
| install | Installation | docs/docs_index.yaml |
| installation_core | Core System Installation | 01-tutorials/INSTALLATION.md |
| intelligence_pattern_learning | Cognitive Intelligence & Pattern Learning |  |
| intelligent_code_navigation | Semantic and Structural Code Navigation |  |
| inter_agent_comm | Inter-Agent Communication |  |
| interactive_controls_implementation | Interactive Dashboard Controls Implementation |  |
| interactive_debugging | Interactive Agent Debugging |  |
| interruption_shielding | Interruption Shielding |  |
| kg_context_retrieval | Knowledge Graph Context Retrieval |  |
| knowledge_graph_migration | ConPort Knowledge Graph Migration |  |
| learning_convergence_validation | Learning Convergence Validation |  |
| litellm_routing_setup | LiteLLM Routing Configuration | 02-how-to/integrations/litellm-claude-code-setup.md |
| manual_correction_supersession | Linear Supersession Management |  |
| mcp-stack-orchestration | MCP Stack Management |  |
| mcp_config_fix | MCP Configuration Fix | mcp-config-fix-summary.md |
| mcp_connectivity | MCP Connectivity & Monitoring |  |
| mcp_management | MCP Server Lifecycle and Configuration |  |
| mcp_recovery | MCP Down Recovery |  |
| mcp_service_discovery | MCP Service Discovery | docs/docs_index.yaml |
| mcp_service_interface |  |  |
| mcp_telemetry | MCP Telemetry Interception |  |
| mcp_token_budgeting | MCP Token Budgeting | docs/best-practices/mcp-token-management.md |
| memory-capture-v1 | Deterministic Memory Capture |  |
| memory_retrieval_ranking | Memory Retrieval and Ranking |  |
| memory_search_retrieval | ADHD-Optimized Memory Search |  |
| meta_prompt_evolution | Meta-Prompt Evolution Cycle |  |
| metrics_benchmarking | Search Metrics Tracking |  |
| metrics_visualization |  |  |
| ml_pattern_learning | ML Pattern Learning & Prediction |  |
| ml_pattern_lifecycle | ML Pattern Learning and Prediction |  |
| ml_task_recommendation | ML-Driven Task Recommendation |  |
| mode_transition | Dashboard Mode Transition |  |
| model_display_setup | LLM Model Display Setup | MODEL_DISPLAY_SETUP.md |
| monitoring_deployment | Monitoring System Deployment Workflow | MONITORING_DEPLOYMENT_GUIDE.md |
| multi_ai_orchestration |  |  |
| multi_directional_sync | Multi-Directional Sync |  |
| multi_engine_search_routing |  |  |
| multi_instance | Multi-Instance Workflow | docs/docs_index.yaml |
| multi_instance_ops | Multi-Instance Operations | 02-how-to/instance-slash-commands.md |
| multi_model_reasoning_mcp | Multi-Model Reasoning (PAL) |  |
| multi_phase_investigation_primer | Multi-Phase Investigation (PRIMER) |  |
| multi_session_management |  |  |
| multi_team_coordination | Cross-Team Dependency Management |  |
| multi_workspace_implementation | Multi-Workspace Service Enhancement Workflow | MULTI_WORKSPACE_IMPLEMENTATION_GUIDE.md |
| multi_workspace_integration | Multi-Workspace Service Integration |  |
| multi_workspace_rollout | Multi-Workspace Support Implementation | ALL_DONE.md |
| observability_and_metrics |  |  |
| orchestrator_agent_coordination | Orchestrator Agent Coordination |  |
| orchestrator_dashboard | Orchestrator Dashboard | docs/docs_index.yaml |
| orchestrator_implementation | Multi-AI Orchestrator Implementation |  |
| orchestrator_state_query | Task Orchestrator State Query |  |
| packet-execution-taskx | Deterministic Packet Execution |  |
| packet_creation | Build Packet Fast |  |
| parallel_ai_orchestration | Parallel Multi-AI Orchestration |  |
| parallel_mcp_execution |  |  |
| partition_reprocessing | Deterministic Partition Reprocessing |  |
| pattern_a_session_envelope | Session Envelope Capture | docs/investigations/deep-research-report 1.md |
| pattern_b_tool_audit | Tool-Call Audit Trail | docs/investigations/deep-research-report 1.md |
| pattern_c_opt_in_injection | Opt-in Injection | docs/investigations/deep-research-report 1.md |
| pattern_d_dual_adapter | Dual Adapter Mode | docs/investigations/deep-research-report 1.md |
| pattern_e_transcript_harvesting | Transcript Harvesting | docs/investigations/deep-research-report 1.md |
| persona_standard_workflow |  |  |
| pipeline_lifecycle_ops | Pipeline Lifecycle Operations |  |
| pm-task-lifecycle | Canonical PM Task Lifecycle |  |
| pm_phase_0_inventory | PM Phase 0: Inventory | docs/planes/pm/HUB.md |
| pm_phase_1_friction | PM Phase 1: Friction Analysis | docs/planes/pm/HUB.md |
| pm_phase_2_adhd_requirements | PM Phase 2: ADHD Requirements | docs/planes/pm/HUB.md |
| pm_phase_3_architecture | PM Phase 3: Architecture | docs/planes/pm/HUB.md |
| pm_phase_4_implementation | PM Phase 4: Implementation | docs/planes/pm/HUB.md |
| pm_phase_5_derived_workflows | PM Phase 5: Derived Workflows | docs/planes/pm/HUB.md |
| pm_plane_initialization | PM Plane Evidence-First Initialization |  |
| postgres_mirror_sync | Postgres Mirror Synchronization |  |
| prd_decomposition |  |  |
| predictive_risk_assessment | ML-Based Risk Assessment |  |
| proactive_intervention | Proactive ADHD Intervention |  |
| production_deployment | Production Deployment Workflow |  |
| production_deployment | Production Stack Deployment | 02-how-to/deployment-guide.md |
| production_readiness | Production Readiness Tracking |  |
| production_readiness_10week | 10-Week Beta Launch Roadmap |  |
| production_readiness_5day | 5-Day Production Readiness Execution |  |
| profile_auto_detection | Profile Auto-Detection Service |  |
| profile_management | Profile Lifecycle Management | 01-tutorials/profile-user-guide.md |
| profile_migration | Profile Migration | docs/docs_index.yaml |
| profile_suggestion_and_switching | Profile Suggestion and Switching |  |
| profile_usage | Profile Usage | docs/docs_index.yaml |
| progressive_kg_exploration | Progressive Knowledge Exploration |  |
| prompt_optimization | Advanced Prompt Optimization |  |
| prompt_optimization_pipeline | Claude Brain Prompt Optimization |  |
| quickstart | Quick Start | docs/docs_index.yaml |
| refactoring_verification | Refactoring Verification |  |
| reflection_cycle | Reflection and Trajectory Update |  |
| registry_configuration_alignment | Registry-Driven Configuration Alignment |  |
| research_operations | ADHD-Optimized Research |  |
| research_task_orchestration |  |  |
| resilient_execution_management |  |  |
| retention_cleanup | Memory Retention Cleanup |  |
| ritual_roasting | Dopamine Ritual Roasting |  |
| role_switching | Role Switching | docs/docs_index.yaml |
| router_orchestration |  |  |
| routing_optimization | Routing and Cost Optimization |  |
| secure_env_management | Secure Environment Management |  |
| security_and_authority | Authentication and Plane Authority |  |
| security_audit_remediation | Security Audit and Vulnerability Remediation |  |
| security_hardening | Security Audit and Hardening |  |
| security_remediation | Security Review and Remediation | PHASE2_SECURITY_REVIEW.md |
| semantic_memory_ops | Semantic Memory Operations |  |
| semantic_search | Task-Aware Semantic Search |  |
| serena_untracked_work_detection | Serena Untracked Work Detection |  |
| service_boot_repair | Service Runtime Boot & Repair |  |
| session_intelligence_tracking |  |  |
| session_recap_generation | Deterministic Session Recap |  |
| session_recovery |  |  |
| session_startup | Start Session Checklist |  |
| single_ai_execution | Single AI Command Execution |  |
| smoke_stack_lifecycle | Smoke Stack Runtime Lifecycle |  |
| stack_lifecycle | Docker Stack Lifecycle Management |  |
| state_monitoring | ADHD State Monitoring |  |
| statusline_redesign | ADHD-Optimized Statusline Redesign |  |
| system_audit | System Audit and Security Review |  |
| system_diagnostics |  |  |
| system_integrity_verification | Continuous System Audit and Verification |  |
| system_maintenance | Stack Maintenance and Audit |  |
| system_resilience | Resilience and Performance Optimization |  |
| system_setup | System Installation and Environment Setup |  |
| task_decomposition | Automatic Task Decomposition |  |
| task_decomposition | Task Decomposition |  |
| task_lifecycle_management | Task Integration and PRD Parsing |  |
| task_orchestration_lifecycle | Task Orchestration & Lifecycle |  |
| task_orchestration_sync |  |  |
| task_packet_execution_contract | Task Packet Execution Contract |  |
| task_suitability_assessment | Task Suitability Assessment |  |
| team_coordination | Event-Driven Team Coordination |  |
| test_failure_rca | Test Failure RCA Loop |  |
| tmux_dashboard_rollout | Tmux Dashboard Phased Rollout |  |
| tmux_layout_and_session_management | Tmux Layout and Session Management |  |
| transcript_ingestion | Copilot Transcript Ingestion |  |
| transient_alerting | Transient Message Alerting |  |
| unified_complexity_scoring | Unified Complexity Coordination |  |
| unified_extraction |  |  |
| unified_health_monitoring | System Health Orchestration |  |
| untracked_work_alignment | Untracked Work Detection & Task Matching |  |
| untracked_work_detection |  |  |
| usage_tracking_reset | Usage Limits Tracking and Reset |  |
| vanilla_agent_lifecycle | Vanilla Agent Lifecycle |  |
| voice_driven_decomposition |  |  |
| voice_status_interface | Voice Status Query |  |
| weekly_insight_generation | Weekly Pattern Reporting |  |
| wf_dashboard_api | Dashboard API Integration |  |
| wf_dashboard_modals | Dashboard Interactive Modals Implementation |  |
| wf_dashboard_streaming | WebSocket Streaming Implementation |  |
| wma_context_recovery | WMA ADHD-Aware Context Recovery |  |
| wma_predictive_restoration | Predictive Context Restoration |  |
| wma_snapshot_capture | WMA Context Snapshot Capture |  |
| workflow_idea_epic_lifecycle | Workflow Idea/Epic Lifecycle | docs/docs_index.yaml |
| working_memory_context_capture |  |  |
| workspace_activity_tracking | Workspace Activity Monitoring |  |
| workspace_context_routing | Workspace Context Injection |  |
| workspace_initialization |  |  |
| workspace_management | Workspace & Global Configuration |  |
| workspace_switch_detection | Workspace Switch Detection |  |
| worktree_auto_config | Worktree Auto-Configuration |  |
| worktree_cli_operations |  |  |
| worktree_lifecycle_management |  |  |
| worktree_optimization | Git Worktree Management |  |
| zen_mcp_development | Zen MCP Tool Development | 02-how-to/DEVELOPING_ZEN.md |
