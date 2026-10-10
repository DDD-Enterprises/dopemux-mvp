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
- **Health Check**: `http://localhost:3001/health`

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

## 🔄 Workflow Servers (Priority: Medium)

### ConPort - Project Memory & Decision Tracking
- **Container**: `mcp-conport`
- **Port**: `3004`
- **Role**: `workflow`
- **Package**: `context-portal-mcp` (uvx)
- **Description**: Knowledge graphs for decisions, progress, and architecture
- **Health Check**: `http://localhost:3004/health`

**Key Features:**
- Cross-session persistence
- Decision rationale tracking
- Project context memory
- Knowledge graph storage

### Task Master AI - Task Management & PRD Processing
- **Container**: `mcp-task-master-ai`
- **Port**: `3005`
- **Role**: `workflow`
- **Package**: `task-master-ai` (uvx)
- **Description**: Natural language task management and PRD parsing
- **Health Check**: `http://localhost:3005/health`

**Key Features:**
- PRD parsing and task generation
- Complexity analysis and dependency tracking
- Natural language task management
- Progress tracking and reporting

### Serena - Code Navigation & Refactoring
- **Container**: `mcp-serena`
- **Port**: `3006`
- **Role**: `workflow`
- **Package**: `serena` (Python module)
- **Description**: LSP functionality, symbol operations, and project memory
- **Health Check**: `http://localhost:3006/health`

**Key Features:**
- Semantic code navigation
- Intelligent refactoring suggestions
- Project context understanding
- Session persistence across development

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

### Leantime - Project Management
- **Network**: `leantime-net` (external)
- **Port**: `8080`
- **Role**: `pm_integration`
- **Description**: Bidirectional task management and project coordination
- **Health Check**: `http://localhost:8080`

**Integration Features:**
- Task import/export workflows
- Status synchronization
- Ownership rules and conflict resolution
- Progress tracking and reporting

## 🔗 Network Architecture

### MCP Network (Internal)
```yaml
network: "mcp-network"
driver: "bridge"
subnet: "172.20.0.0/16"
purpose: "Internal MCP server communication"
```

### Leantime Network (External Bridge)
```yaml
network: "leantime-net"
type: "external"
purpose: "PM system integration"
```

## 📊 Server Monitoring & Health

### Health Check Endpoints
All servers provide standardized health checks:
```bash
curl http://localhost:3002/health  # Context7
curl http://localhost:3003/health  # Zen
curl http://localhost:3001/health  # Sequential Thinking
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
docker-compose up -d context7           # Start Context7
docker-compose restart zen              # Restart Zen
docker-compose logs -f sequential-thinking  # View logs
```

### Health Check All Critical Servers
```bash
for port in 3001 3002 3003; do
  curl -sf "http://localhost:$port/health" && echo "✅ Port $port healthy" || echo "❌ Port $port unhealthy"
done
```

---

**📈 Implementation Status**: All servers documented and containerized
**🎯 Next Phase**: MetaMCP orchestration development