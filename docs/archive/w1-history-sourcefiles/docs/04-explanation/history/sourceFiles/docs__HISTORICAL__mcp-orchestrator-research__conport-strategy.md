
  🚀 Enhanced Dopemux MCP Orchestration with ConPort Integration

  Key Insights from Your ConPort Strategy

  1. Workspace-based memory with automatic initialization
  2. Proactive context management throughout sessions
  3. Rich knowledge graph with item linking
  4. Semantic search capabilities for complex queries
  5. Automatic sync routines for maintaining context

  Updated Architecture

  # docker/docker-compose.yml
  version: '3.8'

  networks:
    dopemux-net:
      driver: bridge

  services:
    # === INFRASTRUCTURE LAYER ===
    postgres:
      image: postgres:15-alpine
      container_name: dopemux-postgres
      environment:
        POSTGRES_DB: dopemux
        POSTGRES_USER: dopemux
        POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      volumes:
        - postgres_data:/var/lib/postgresql/data
        - ./infrastructure/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U dopemux"]
        interval: 10s
        timeout: 5s
        retries: 5

    redis:
      image: redis:7-alpine
      container_name: dopemux-redis
      command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
      volumes:
        - redis_data:/data
      healthcheck:
        test: ["CMD", "redis-cli", "ping"]

    milvus:
      image: milvusdb/milvus:latest
      container_name: dopemux-milvus
      environment:
        ETCD_ENDPOINTS: etcd:2379
        MINIO_ADDRESS: minio:9000
      depends_on:
        - etcd
        - minio

    # === MCP SERVERS LAYER ===

    # ConPort - Project Memory & Knowledge Graph
    conport:
      build: ./mcp-servers/conport
      container_name: dopemux-conport
      environment:
        DATABASE_URL: postgresql://dopemux:${POSTGRES_PASSWORD}@postgres:5432/dopemux
        REDIS_URL: redis://default:${REDIS_PASSWORD}@redis:6379
        WORKSPACE_ROOT: /workspace
      volumes:
        - ${PWD}:/workspace:ro
        - conport_data:/app/context_portal
      depends_on:
        postgres:
          condition: service_healthy
        redis:
          condition: service_started

    # OpenMemory - Cross-session Memory
    openmemory:
      build: ./mcp-servers/openmemory
      container_name: dopemux-openmemory
      environment:
        DATABASE_URL: postgresql://dopemux:${POSTGRES_PASSWORD}@postgres:5432/dopemux
        MEM0_API_KEY: ${MEM0_API_KEY}
      depends_on:
        postgres:
          condition: service_healthy

    # Desktop Commander - UI Automation
    desktop-commander:
      build: ./mcp-servers/desktop-commander
      container_name: dopemux-desktop-commander
      environment:
        DISPLAY: ${DISPLAY:-:0}
      volumes:
        - /tmp/.X11-unix:/tmp/.X11-unix:rw
        - ${HOME}/.Xauthority:/root/.Xauthority:ro
      network_mode: host

    # GitHub - Repository Integration
    github:
      build: ./mcp-servers/github
      container_name: dopemux-github
      environment:
        GITHUB_TOKEN: ${GITHUB_TOKEN}
        GITHUB_API_URL: https://api.github.com

    # MAS Sequential Thinking
    mas-sequential-thinking:
      build:
        context: /Users/hue/code/mcp-server-mas-sequential-thinking
        dockerfile: Dockerfile
      container_name: dopemux-mas-sequential-thinking
      environment:
        LLM_PROVIDER: ${LLM_PROVIDER:-deepseek}
        OPENAI_API_KEY: ${OPENAI_API_KEY}
        DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY}
      volumes:
        - mas_sessions:/app/sessions

    # Zen - Multi-model Orchestration
    zen:
      build: ./mcp-servers/zen
      container_name: dopemux-zen
      environment:
        OPENAI_API_KEY: ${OPENAI_API_KEY}
        ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
        GEMINI_API_KEY: ${GEMINI_API_KEY}
        GROQ_API_KEY: ${GROQ_API_KEY}
        ZEN_DISABLED_TOOLS: "chat,explain,translate,summarize"

    # Claude Context - Semantic Search
    claude-context:
      build: ./mcp-servers/claude-context
      container_name: dopemux-claude-context
      environment:
        MILVUS_ADDRESS: milvus:19530
        EMBEDDING_PROVIDER: local
        OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      depends_on:
        - milvus

    # Context7 - Documentation
    context7:
      build: ./mcp-servers/context7
      container_name: dopemux-context7

    # Morphllm Fast Apply
    morphllm-fast-apply:
      build: ./mcp-servers/morphllm-fast-apply
      container_name: dopemux-morphllm

    # Exa - Web Search
    exa:
      build: ./mcp-servers/exa
      container_name: dopemux-exa
      environment:
        EXA_API_KEY: ${EXA_API_KEY}

    # === ORCHESTRATION LAYER ===

    # MetaMCP Orchestrator
    orchestrator:
      build: ./orchestrator
      container_name: dopemux-orchestrator
      environment:
        POSTGRES_URL: postgresql://dopemux:${POSTGRES_PASSWORD}@postgres:5432/dopemux
        REDIS_URL: redis://default:${REDIS_PASSWORD}@redis:6379
        MAX_TOKENS: 10000
        DEFAULT_ROLE: researcher
      volumes:
        - ./orchestrator/config:/app/config:ro
        - ${PWD}:/workspace:ro
      depends_on:
        - postgres
        - redis
      ports:
        - "8000:8000"  # WebSocket endpoint for Claude

  volumes:
    postgres_data:
    redis_data:
    milvus_data:
    conport_data:
    mas_sessions:

  Enhanced Command System with ConPort Integration

  # .claude/commands/dopemux-bootstrap.md
  # Bootstrap a Dopemux session with full context awareness

  1. **Initialize ConPort Memory**
     - Determine workspace_id from ${workspaceFolder}
     - Check for existing context_portal/context.db
     - If exists: Load product_context, active_context, recent_activity
     - If not: Bootstrap from projectBrief.md if available

  2. **Session Orchestrator Initialization**
     - Auto-index codebase with claude-context
     - Load previous session state from openmemory
     - Identify active tasks from ConPort progress items
     - Suggest starting role based on context

  3. **Role Detection & Tool Loading**
     - Analyze current context to determine optimal role
     - Load only necessary tools (<10k tokens)
     - Set up telemetry tracking

  4. **Status Report**
     - [CONPORT_ACTIVE] or [CONPORT_INACTIVE]
     - [ROLE: researcher|implementer|reviewer|...]
     - [TOKENS: XXXX/10000]
     - Recent activity summary
     - Suggested next actions

  Advanced ConPort-Aware Commands

  # .claude/commands/context-sync.md
  # Synchronize all context sources

  <thinking>
  - Need to sync ConPort, OpenMemory, and session state
  - Check for changes in current chat session
  - Update all relevant context stores
  </thinking>

  1. Invoke ConPort sync routine
  2. Update OpenMemory with session decisions
  3. Store patterns in memory-bank
  4. Update telemetry
  5. Report sync status

  # .claude/commands/knowledge-graph.md
  # Visualize and manage knowledge graph

  1. Get all ConPort linked items
  2. Generate relationship map
  3. Identify orphaned items
  4. Suggest new links based on context
  5. Export to markdown or mermaid diagram

  # .claude/commands/semantic-search.md
  # Advanced semantic search across all memory sources

  1. Search ConPort with semantic_search_conport
  2. Search OpenMemory collections
  3. Search claude-context codebase
  4. Aggregate and rank results
  5. Present unified view

  Role Definitions with ConPort Integration

  # docker/orchestrator/config/roles.yaml
  roles:
    session_orchestrator:
      description: "Automated session management role"
      max_tokens: 5000
      auto_run: true
      tools:
        - conport:
            - get_product_context
            - get_active_context
            - update_active_context
            - get_recent_activity_summary
            - log_progress
        - claude-context:
            - index_codebase
            - search_code
        - openmemory:
            - store
            - retrieve
        - github:
            - get_issues
      triggers:
        - on_session_start:
            actions:
              - "conport.get_recent_activity_summary"
              - "claude-context.index_codebase"
              - "openmemory.retrieve(last_session)"
        - every_25_minutes:
            actions:
              - "conport.update_active_context"
              - "openmemory.store(checkpoint)"
        - on_context_switch:
            actions:
              - "conport.log_progress"
              - "telemetry.log_transition"

    researcher:
      description: "Research and exploration role"
      max_tokens: 8000
      tools:
        - context7: [resolve-library-id, get-library-docs]
        - exa: [exa_search]
        - github: [search_issues, search_code]
        - conport:
            - get_product_context
            - search_decisions_fts
            - search_custom_data_value_fts
            - semantic_search_conport

    implementer:
      description: "Code implementation role"
      max_tokens: 10000
      tools:
        - morphllm-fast-apply: [edit_file]
        - claude-context: [search_code]
        - conport:
            - get_active_context
            - log_progress
            - update_progress
        - desktop-commander: [screenshot, execute_command]

    reviewer:
      description: "Code review and quality assurance"
      max_tokens: 9000
      tools:
        - zen: [codereview, consensus, precommit]
        - github: [create_pr_review, add_comment]
        - conport:
            - log_decision
            - get_system_patterns
            - link_conport_items

    architect:
      description: "System design and planning"
      max_tokens: 10000
      tools:
        - zen: [planner, thinkdeep]
        - mas-sequential-thinking: [sequentialthinking]
        - conport:
            - update_product_context
            - log_system_pattern
            - log_decision
            - link_conport_items

  Workflow Integration with ConPort

  # src/dopemux/orchestration/workflows.py

  class DopemuxWorkflow:
      """Enhanced workflow with ConPort memory integration"""

      async def research_workflow(self):
          """Research workflow with automatic context capture"""
          # 1. Load product context
          product_context = await self.conport.get_product_context()

          # 2. Search for relevant decisions
          prior_decisions = await self.conport.search_decisions_fts(
              query_term=self.current_topic
          )

          # 3. Perform research with context
          research_results = await self.context7.get_library_docs(
              context=product_context
          )

          # 4. Store findings
          await self.conport.log_custom_data(
              category="research_findings",
              key=f"research_{timestamp}",
              value=research_results
          )

          # 5. Update active context
          await self.conport.update_active_context(
              patch_content={
                  "current_focus": "research",
                  "last_research": research_results.summary
              }
          )

      async def implementation_workflow(self):
          """Implementation with progress tracking"""
          # 1. Get current task from ConPort
          active_tasks = await self.conport.get_progress(
              status_filter="IN_PROGRESS"
          )

          # 2. Implementation loop
          for task in active_tasks:
              # Update progress
              await self.conport.update_progress(
                  progress_id=task.id,
                  status="IN_PROGRESS",
                  description=f"Working on: {task.description}"
              )

              # Do implementation
              result = await self.morphllm.edit_file(...)

              # Log completion
              await self.conport.update_progress(
                  progress_id=task.id,
                  status="DONE"
              )

              # Link to any decisions
              if task.linked_item_type == "decision":
                  await self.conport.link_conport_items(
                      source_item_type="progress",
                      source_item_id=task.id,
                      target_item_type="decision",
                      target_item_id=task.linked_item_id,
                      relationship_type="implements"
                  )

  Session Lifecycle with ConPort

  # src/dopemux/orchestration/session_orchestrator.py

  class SessionOrchestrator:
      """Automated session management with ConPort integration"""

      async def initialize_session(self):
          """Full session initialization following ConPort strategy"""
          workspace_id = os.environ.get('WORKSPACE_FOLDER', os.getcwd())

          # Check for existing ConPort database
          conport_db = Path(workspace_id) / "context_portal" / "context.db"

          if conport_db.exists():
              # Load existing context
              product_ctx = await self.conport.get_product_context(workspace_id)
              active_ctx = await self.conport.get_active_context(workspace_id)
              recent_activity = await self.conport.get_recent_activity_summary(
                  workspace_id=workspace_id,
                  hours_ago=24
              )

              # Set status
              self.conport_status = "CONPORT_ACTIVE"

              # Analyze context to suggest role
              suggested_role = self.analyze_context_for_role(
                  active_ctx, recent_activity
              )
          else:
              # Bootstrap new ConPort
              project_brief = Path(workspace_id) / "projectBrief.md"
              if project_brief.exists():
                  content = project_brief.read_text()
                  await self.conport.update_product_context(
                      workspace_id=workspace_id,
                      content={"initial_product_brief": content}
                  )

              self.conport_status = "CONPORT_ACTIVE"
              suggested_role = "researcher"  # Default for new projects

          # Load role tools
          await self.orchestrator.switch_role(suggested_role)

          # Return status
          return {
              "status": self.conport_status,
              "role": suggested_role,
              "tokens": self.orchestrator.current_tokens,
              "recent_activity": recent_activity
          }

      async def checkpoint(self):
          """ADHD-friendly checkpoint every 25 minutes"""
          # Update ConPort active context
          await self.conport.update_active_context(
              patch_content={
                  "last_checkpoint": datetime.now().isoformat(),
                  "current_tokens": self.orchestrator.current_tokens,
                  "session_duration": self.session_duration
              }
          )

          # Store to OpenMemory
          await self.openmemory.store(
              key=f"checkpoint_{datetime.now().isoformat()}",
              value={
                  "role": self.current_role,
                  "context": self.current_context,
                  "progress": self.completed_tasks
              }
          )

          # Suggest break
          return {
              "message": "25-minute checkpoint reached",
              "suggestion": "Take a 5-minute break",
              "next_task": self.suggest_next_task()
          }

  Key Enhancements from ConPort Strategy

  1. Automatic Context Loading: Every session starts with ConPort initialization
  2. Proactive Linking: AI suggests knowledge graph connections
  3. Dynamic RAG: Semantic search across all memory sources
  4. Sync Routines: Regular synchronization of all context
  5. Rich Telemetry: Track everything for optimization

  This creates a truly intelligent orchestration system that:
  - Maintains persistent memory across sessions
  - Automatically manages context and roles
  - Tracks all decisions and progress
  - Builds a knowledge graph of your project
  - Optimizes for ADHD with regular checkpoints
  - Provides rich telemetry for improvement

  The combination of Docker containerization, role-based loading, ConPort memory strategy, and workflow automation
  creates the ultimate development environment!