# 🗂️ Dopemux MCP Server Registry

Complete registry of all MCP servers in the Dopemux orchestration, organized by priority and role according to ADR-007 and ADR-012.

## 📚 Critical Path Servers (Priority: Highest)

### Context7 - Documentation & API References
- **Container**: `mcp-context7`
- **Port**: `3002`
- **Role**: `critical_path`
- **Package**: `@upstash/context7:^1.0.17`
- **Description**: ALWAYS FIRST for any code work - provides official documentation and API references
- **Health Check**: `http://localhost:3002/health`
- **Configuration**: `/docker/mcp-servers/context7/.env`

**Key Features:**
- Up-to-date, version-specific documentation
- Official API patterns and examples
- Integration with 400+ libraries
- Eliminates hallucinations through authoritative sources

**Usage Pattern:**
```yaml
rule: "MANDATORY first query for ANY code generation"
fallback: "Only use Exa if Context7 lacks information"
optimization: "max_results: 10, focus_on_examples: true"
```

### Zen - Multi-Model Orchestration
- **Container**: `mcp-zen`
- **Port**: `3003`
- **Role**: `critical_path`
- **Source**: `/Users/hue/code/zen-mcp-server`
- **Description**: Orchestrates multiple AI models (GPT-5, Gemini, DeepSeek) for complex decisions
- **Health Check**: `http://localhost:3003/health`

**Key Features:**
- Multi-model consensus for architectural decisions
- Chat, thinkdeep, planner, consensus tools
- Code review and debugging capabilities
- Model routing and conversation continuity

**Usage Pattern:**
```yaml
use_for: "Complex architectural decisions, code reviews, debugging"
models: ["GPT-5", "Gemini Pro", "DeepSeek", "Claude"]
tools: ["chat", "thinkdeep", "planner", "consensus", "debug", "codereview"]
```

### Sequential Thinking - Multi-Step Reasoning
- **Container**: `mcp-mas-sequential-thinking`
- **Port**: `3001`
- **Role**: `critical_path`
- **Source**: `https://github.com/FradSer/mcp-server-mas-sequential-thinking.git`
- **Description**: Multi-agent system for complex reasoning and architectural analysis
- **Health Check**: Port liveness `3001` (no `/health`)

**Key Features:**
- Multi-step hypothesis testing
- Complex problem decomposition
- Systematic debugging approach
- Architectural reasoning support

**Usage Pattern:**
```yaml
use_for: "Complex debugging, system design, multi-component analysis"
max_thinking_steps: 10
enable_context_preservation: true
```

**Start/Inspect:**
```bash
cd docker/mcp-servers
./start-mas.sh                                        # Build and start
docker-compose logs -f mas-sequential-thinking        # Tail logs
# Broker (HTTP): http://localhost:3001
# Liveness test (port): nc -z localhost 3001 && echo "up" || echo "down"
```

## 🔄 Workflow Servers (Priority: Medium)

### ConPort - Project Memory & Decision Tracking
- **Container**: `mcp-conport`
- **Port**: `3004`
- **Role**: `workflow`
- **Package**: `context-portal-mcp` (uvx)
- **Description**: Foundational graph store for decisions, progress, and architectural context
- **Health Check**: `http://localhost:3004/health`

**Authority Scope:**
- **Decision Storage**: Authoritative repository for all architectural and implementation decisions
- **Knowledge Graph**: Primary source for project context, relationships, and decision history
- **Cross-Session Memory**: Persistent context across interruptions, sessions, and team members
- **Pattern Recognition**: Historical analysis of decisions and their outcomes

**Key Features:**
- Foundational graph store for entire ecosystem
- Decision rationale tracking with full context
- Cross-session persistence and context restoration
- Knowledge graph relationships between decisions, tasks, code, and patterns
- ADHD-optimized context preservation

**Foundational Role:**
- **Serves ALL Systems**: Task-Master, Task-Orchestrator, Leantime, Serena, Integration Bridge
- **Persistent Memory**: Maintains context across the entire Two-Plane Architecture
- **Decision Authority**: Single source of truth for "why we made this choice"
- **Context Bridge**: Connects decisions to code changes, tasks, and outcomes

### Task Master AI - Task Management & PRD Processing
- **Container**: `mcp-task-master-ai`
- **Port**: `3005`
- **Role**: `workflow`
- **Package**: `task-master-ai` (uvx)
- **Description**: Natural language task management and PRD parsing
- **Health Check**: `http://localhost:3005/health`

**Authority Scope:**
- **PRD Analysis**: Authoritative for parsing and understanding PRDs
- **Task Creation**: Primary source for initial task breakdown
- **Requirements Interpretation**: AI-powered analysis of natural language requirements
- **Task Hierarchy**: Initial structure and relationship definition

**Key Features:**
- PRD parsing and task generation
- Complexity analysis and dependency tracking
- Natural language task management
- AI-powered requirement analysis

**Integration Boundaries:**
- **Hands off to**: Task-Orchestrator for dependency analysis and execution planning
- **Coordinates with**: ConPort for decision logging, Integration Bridge for workflow orchestration
- **Does NOT**: Manage task status (Leantime authority), handle code context (Serena authority)

### Task Orchestrator - Dependency Analysis & Task Orchestration
- **Container**: `mcp-task-orchestrator`
- **Port**: `3014`
- **Role**: `workflow`
- **Repository**: `https://github.com/jpicklyk/task-orchestrator`
- **Description**: Advanced dependency analysis and task orchestration with 37 specialized tools
- **Health Check**: `http://localhost:3014/health`
- **Technology**: Kotlin, specialized orchestration algorithms

**Authority Scope:**
- **Dependency Analysis**: Authoritative for task dependency relationships and conflict resolution
- **Execution Planning**: Primary source for task scheduling and workflow optimization
- **File Context**: Provides code file and symbol context for development tasks
- **Complexity Scoring**: Authoritative for task complexity analysis (1-10 scale)

**Key Features:**
- Dependency analysis and conflict resolution
- Task scheduling and execution planning
- 37 specialized orchestration tools
- Cross-project dependency tracking
- File context provision for Serena LSP

**Integration Boundaries:**
- **Receives from**: Task-Master-AI for initial task breakdown
- **Hands off to**: Leantime Bridge for status management and team coordination
- **Provides to**: Serena LSP for file and symbol context during development
- **Coordinates with**: Integration Bridge for execution workflow, ConPort for dependency decisions
- **Does NOT**: Create or modify tasks (Task-Master authority), manage status (Leantime authority)

### Serena - ADHD-Optimized Code Navigation & Project Memory
- **Container**: `mcp-serena`
- **Port**: `3006`
- **Role**: `workflow`
- **Package**: `serena` (Python module via uvx or pip)
- **Description**: Full LSP server with ADHD accommodations for code navigation and developer working memory
- **Health Check**: `http://localhost:3006/health`
- **Source**: `/services/serena/server.py` (MCP wrapper with event integration)

**Authority Scope:**
- **Code Navigation**: Authoritative for semantic code search, symbol navigation, and file exploration
- **LSP Operations**: Full Language Server Protocol implementation (completion, diagnostics, hover, references)
- **Developer Memory**: Working memory preservation, session context, navigation breadcrumbs
- **Code Intelligence**: Refactoring suggestions, complexity analysis, architectural insights
- **ADHD Accommodations**: Attention-aware UI, progressive disclosure, cognitive load management

**Key Features:**
- Full LSP server capabilities (completion, diagnostics, go-to-definition, find references)
- Semantic code navigation with progressive disclosure
- Intelligent refactoring suggestions categorized by complexity/risk
- Project context understanding with depth limiting (default: 3 levels)
- Session persistence and navigation breadcrumbs
- ADHD accommodations: max 10 search results, gentle guidance
- Event bus integration for attention coordination

**Integration Boundaries:**
- **Receives from**: Task-Orchestrator for file and symbol context when working on specific tasks
- **Coordinates with**: ConPort for decision logging during code changes, Event Bus for attention state
- **Provides to**: Developers through LSP protocol, Integration Bridge for progress updates
- **Does NOT**: Create or manage tasks (Task-Master/Orchestrator authority), determine project priorities (Leantime authority)

**ADHD Configuration:**
```yaml
max_search_results: 10          # Prevent overwhelming results
context_depth: 3                # Limit context complexity
progressive_disclosure: true    # Show essential info first
navigation_breadcrumbs: true    # Track navigation history
intelligent_suggestions: true   # Categorize by complexity
gentle_guidance: true          # Supportive feedback
```

**Cognitive Plane Role:**
```yaml
focus: "HOW a developer works (vs WHAT needs to be done)"
capabilities: ["code_understanding", "navigation_assistance", "working_memory", "attention_management"]
complements: ["Task-Master-AI (WHAT)", "Task-Orchestrator (WHEN)", "Leantime (STATUS)"]
```

### Claude Context - Semantic Code Search
- **Container**: `mcp-claude-context`
- **Port**: `3007`
- **Role**: `research`
- **Package**: `@zilliz/claude-context-mcp@latest`
- **Description**: Repository-wide semantic search and context understanding
- **Health Check**: `http://localhost:3007/health`

**Key Features:**
- Vector-based code search
- Context understanding and symbol navigation
- Integration with Milvus vector database
- Repository-wide pattern detection

## 🧠 Research Servers (Deep Research)

### GPT Researcher - Autonomous Deep Research
- **Container**: `mcp-gptr-mcp`
- **Port**: `3009`
- **Role**: `research`
- **Source**: `https://github.com/assafelovic/gptr-mcp`
- **Description**: Autonomous deep research with multi-agent exploration and comprehensive reports
- **Health Check**: `http://localhost:3009/health`

**Key Features:**
- Tree-like exploration (depth/breadth controls)
- Source gathering and citation
- Report generation (markdown/HTML/JSON)
- Useful for longer investigations and synthesis

**Start/Inspect:**
```bash
cd docker/mcp-servers
./start-gptr.sh                           # Build, start, and health-check
docker-compose logs -f gptr-mcp           # Tail logs
```

### GPT Researcher (STDIO) - Proxy Exec Container
- **Container**: `mcp-gptr-stdio`
- **Port**: n/a (stdio via exec)
- **Role**: `research`
- **Description**: Keeps a light container running so the proxy can exec the stdio MCP server

**Start/Inspect:**
```bash
cd docker/mcp-servers
./start-gptr-stdio.sh                      # Build helper container
docker exec -it mcp-gptr-stdio python /app/scripts/gpt-researcher/mcp_server.py  # Manual run
# Proxy named-server (used by scripts):
#  gptr-researcher-stdio -> docker exec -i mcp-gptr-stdio python /app/scripts/gpt-researcher/mcp_server.py
```

## 🔧 Quality & Utility Servers (Priority: Medium-Low)

### Exa - Web Research (Fallback Only)
- **Container**: `mcp-exa`
- **Port**: `3008`
- **Role**: `research`
- **Package**: `exa-mcp` (npm)
- **Description**: Web research - ONLY when Context7 lacks information
- **Health Check**: `http://localhost:3008/health`

**Key Features:**
- Real-time web search and research
- Community solutions and best practices
- Current trends and documentation
- Fallback for Context7 gaps

**Usage Pattern:**
```yaml
rule: "ONLY use when Context7 lacks required information"
optimization: "min_query_length: 10, max_results: 3"
```

### MorphLLM Fast Apply - Pattern-Based Transformations
- **Container**: `mcp-morphllm-fast-apply`
- **Port**: `3011`
- **Role**: `quality`
- **Package**: `morphllm-fast-apply` (uvx)
- **Description**: Bulk edits, pattern-based transformations, and style enforcement
- **Health Check**: `http://localhost:3011/health`

**Key Features:**
- Large-scale refactoring operations
- Pattern application across codebases
- Style enforcement and migrations
- Framework updates and modernization

### Desktop Commander - Desktop Automation
- **Container**: `mcp-desktop-commander`
- **Port**: `3012`
- **Role**: `utility`
- **Description**: Desktop automation and system control for ADHD workflows
- **Health Check**: `http://localhost:3012/health`

**Key Features:**
- Screenshot capture and analysis
- Window management and focus control
- Text input automation
- Desktop workflow integration

## 📋 External Integrations

### Integration Bridge - Two-Plane Coordinator
- **Container**: `mcp-integration-bridge`
- **Port**: `3016`
- **Role**: `critical_path`
- **Package**: Custom FastAPI service
- **Description**: Central coordination layer for Two-Plane Architecture task management
- **Health Check**: `http://localhost:3016/health`
- **Source**: `/services/mcp-integration-bridge/`

**Key Features:**
- Coordinates Project Management Plane (Task-Master + Task-Orchestrator + Leantime)
- Interfaces with Cognitive Plane (Serena + ConPort)
- Multi-instance coordination via shared database
- ADHD-friendly progress tracking and celebrations
- Template-based workflow creation
- Real-time dependency resolution

**Two-Plane Integration:**
```yaml
project_management_plane:
  - task_master_ai: "PRD breakdown and analysis"
  - task_orchestrator: "Dependency analysis with 37 tools"
  - leantime_bridge: "Status authority and team dashboards"

cognitive_plane:
  - serena: "LSP server with ADHD code navigation"
  - conport: "Decision memory and knowledge graph"

coordination: "Integration Bridge manages data flow between planes"
```

### Leantime Bridge - Status Authority
- **Container**: `mcp-leantime-bridge`
- **Port**: `3015`
- **Role**: `workflow`
- **Package**: Custom Python MCP bridge
- **Description**: Master authority for task status and team coordination
- **Health Check**: `http://localhost:3015/health`

**Authority Scope:**
- **Task Status**: Authoritative source for planned/active/blocked/completed
- **Team Dashboards**: Primary interface for project visibility
- **Milestone Tracking**: Sprint and project milestone management
- **Assignments**: Task ownership and team coordination

**Integration Features:**
- Bidirectional sync with Task-Master-AI and Task-Orchestrator
- Status broadcast to all systems via Integration Bridge
- Team dashboard and reporting capabilities
- Conflict resolution for cross-system updates

### Leantime - Project Management
- **Network**: `leantime-net` (external)
- **Port**: `8080`
- **Role**: `pm_integration`
- **Description**: External Leantime instance for comprehensive project management
- **Health Check**: `http://localhost:8080`

**Integration Features:**
- Connected via Leantime Bridge (Port 3015)
- Web interface for team collaboration
- Advanced project management features
- Reporting and analytics dashboard

## 🔗 Network Architecture

### MCP Network (External)
```yaml
network: "mcp-network"
type: "external"
purpose: "Shared network for MCP servers across projects"
```

### Leantime Network (External Bridge)
```yaml
network: "leantime-net"
type: "external"
purpose: "PM system integration"
```

## 📊 Server Monitoring & Health

### Health Check Endpoints
Most servers expose `/health`. MAS uses a port-liveness check:
```bash
curl http://localhost:3002/health  # Context7
curl http://localhost:3003/health  # Zen
nc -z localhost 3001 && echo "MAS up" || echo "MAS down"  # Sequential Thinking (no /health)
# ... etc for all servers
```

### Service Discovery Labels
```yaml
labels:
  - "mcp.role={critical_path|workflow|research|quality|utility}"
  - "mcp.priority={highest|high|medium|low}"
  - "mcp.description={human readable description}"
```

## 🚀 Quick Reference

### Start All Servers
```bash
cd /Users/hue/code/dopemux-mvp/docker/mcp-servers
./start-all-mcp-servers.sh
```

### Individual Server Control
```bash
docker-compose up -d context7                 # Start Context7
docker-compose restart zen                    # Restart Zen
docker-compose logs -f mas-sequential-thinking  # View MAS logs
```

### Health Check All Critical Servers
```bash
for port in 3001 3002 3003; do
  if [ "$port" -eq 3001 ]; then
    nc -z localhost 3001 && echo "✅ MAS (3001) up" || echo "❌ MAS (3001) down"
  else
    curl -sf "http://localhost:$port/health" && echo "✅ Port $port healthy" || echo "❌ Port $port unhealthy"
  fi
done
```

---

**📈 Implementation Status**: All servers documented and containerized
**🎯 Next Phase**: MetaMCP orchestration development
