# 📦 MCP Server Specifications

## Overview

Detailed specifications for each MCP server in the Dopemux ecosystem, including configuration, Docker setup, and integration points.

## Core MCP Servers

### 1. ConPort - Project Memory & Knowledge Graph

**Purpose**: Persistent project context with semantic search and knowledge graph capabilities

**Docker Configuration**:
```dockerfile
FROM node:20-alpine
RUN npm install -g context-portal-mcp@latest
WORKDIR /app
ENV AUTO_DETECT_WORKSPACE=true
ENV WORKSPACE_SEARCH_START=/workspace
ENV SEMANTIC_SEARCH_ENABLED=true
CMD ["conport-mcp", "--mode", "stdio", "--log-level", "INFO"]
```

**Integration Points**:
- PostgreSQL for persistent storage
- Redis for caching
- Workspace volume mount
- mem4sprint strategy implementation

**Key Features**:
- Automatic workspace detection
- Product/Active context management
- Decision logging with FTS
- Progress tracking
- System patterns
- Custom data with categories
- Semantic search
- Knowledge graph linking
- Import/Export to markdown

**ADHD Optimizations**:
- Auto-saves context every 30 seconds
- Visual breadcrumbs for navigation
- Quick bookmark creation
- Pattern recognition for repeated tasks

### 2. OpenMemory (Mem0) - Cross-Session Memory

**Purpose**: Long-term memory that persists across sessions and projects

**Docker Configuration**:
```dockerfile
FROM python:3.11-slim
RUN pip install mem0ai pymongo redis psycopg2-binary
WORKDIR /app
ENV MEM0_CONFIG_PATH=/config/mem0.yaml
ENV CROSS_SESSION_MEMORY=true
CMD ["python", "-m", "mem0.server"]
```

**Integration Points**:
- PostgreSQL for structured memory
- MongoDB for document storage
- Redis for fast retrieval
- Vector embeddings for similarity search

**Key Features**:
- User preferences persistence
- Decision history
- Learning patterns
- Cross-project knowledge
- Relationship mapping

**ADHD Optimizations**:
- Automatic context switching detection
- Preference learning (best times, energy levels)
- Pattern-based suggestions

### 3. Zen - Multi-Model Orchestration

**Purpose**: Coordinate multiple AI models for complex reasoning

**Docker Configuration**:
```dockerfile
FROM node:20-alpine
RUN npm install -g zen-mcp@latest
WORKDIR /app
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ENV ZEN_DISABLED_TOOLS="chat,explain,translate,summarize,analyze,refactor,testgen,secaudit,docgen,tracer"
ENV DEFAULT_THINKING_MODE=low
CMD ["zen-mcp"]
```

**Available Tools**:
- `debug` - Deep debugging assistance
- `precommit` - Pre-commit checks
- `planner` - Project planning
- `codereview` - Code review
- `consensus` - Multi-model consensus
- `challenge` - Challenge assumptions
- `thinkdeep` - Deep analysis

**Model Selection**:
```yaml
models:
  planning: gemini-pro
  coding: gpt-4
  review: claude-3
  debug: o3-mini
```

**ADHD Optimizations**:
- Conservative token usage (low mode)
- Quick model switching
- Focused tool selection per role

### 4. MAS Sequential Thinking

**Purpose**: Structured multi-step reasoning for complex problems

**Docker Configuration**:
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV LLM_PROVIDER=deepseek
ENV LOG_LEVEL=INFO
CMD ["python", "main.py"]
```

**Key Features**:
- Team-based reasoning
- Session memory
- Step-by-step breakdown
- Thought validation

**ADHD Optimizations**:
- Visual progress through reasoning steps
- Checkpoint-able thinking sessions
- Resume from interruption

### 5. Claude-Context - Semantic Code Search

**Purpose**: Intelligent code search with semantic understanding

**Docker Configuration**:
```dockerfile
FROM node:20-alpine
RUN npm install -g @zilliz/claude-context-mcp@latest
WORKDIR /app
ENV MILVUS_ADDRESS=milvus:19530
ENV EMBEDDING_PROVIDER=local
ENV HYBRID_SEARCH=true
ENV BM25_WEIGHT=0.3
ENV VECTOR_WEIGHT=0.7
CMD ["claude-context-mcp"]
```

**Integration Points**:
- Milvus vector database
- Local embeddings generation
- AST-based code splitting
- Automatic indexing

**ADHD Optimizations**:
- Hot file detection
- Recent change prioritization
- Visual code maps

### 6. Task-Master AI - Intelligent Task Management

**Purpose**: Parse requirements and create actionable tasks

**Docker Configuration**:
```dockerfile
FROM python:3.11-slim
RUN pip install task-master-ai
WORKDIR /app
ENV TASK_DECOMPOSITION_MODEL=gpt-4
ENV MAX_TASK_SIZE=4_hours
ENV ADHD_MODE=true
CMD ["python", "-m", "task_master.server"]
```

**Key Features**:
- PRD parsing
- Epic → Story → Task breakdown
- Time estimation
- Dependency mapping
- Priority scoring

**ADHD Optimizations**:
- Automatic chunking to 25-min blocks
- Energy level matching
- Focus type categorization
- Dopamine checkpoint insertion

### 7. Leantime - Agile Project Management

**Purpose**: Full agile/scrum support with ADHD accommodations

**Docker Configuration**:
```yaml
leantime:
  image: leantime/leantime:latest
  environment:
    LEAN_DB_HOST: postgres
    LEAN_SITENAME: "Dopemux PM"
    LEAN_ADHD_MODE: "true"
    LEAN_DEFAULT_SPRINT: "25min"
  volumes:
    - leantime_data:/var/www/html/userfiles
```

**Integration Points**:
- MySQL/PostgreSQL backend
- REST API for automation
- Calendar sync
- Slack/Discord webhooks

**ADHD Optimizations**:
- Visual kanban boards
- Sprint timer integration
- Automatic standup reminders
- Progress celebrations

### 8. Desktop-Commander - UI Automation

**Purpose**: Control desktop applications and capture context

**Docker Configuration**:
```dockerfile
FROM node:20-alpine
RUN apk add --no-cache xvfb x11vnc fluxbox
RUN npm install -g desktop-commander-mcp
ENV DISPLAY=:99
ENV SCREENSHOT_PATH=/screenshots
CMD ["desktop-commander-mcp"]
```

**Key Features**:
- Screenshot capture
- Click automation
- Window management
- Text extraction

**ADHD Optimizations**:
- Visual context capture
- Automatic window organization
- Distraction hiding

### 9. GitHub - Repository Integration

**Purpose**: Seamless GitHub integration for issues, PRs, and code

**Docker Configuration**:
```dockerfile
FROM node:20-alpine
RUN npm install -g github-mcp
ENV GITHUB_TOKEN=${GITHUB_TOKEN}
ENV GITHUB_DEFAULT_OWNER=${GITHUB_OWNER}
ENV GITHUB_DEFAULT_REPO=${GITHUB_REPO}
CMD ["github-mcp"]
```

**Key Features**:
- Issue management
- PR creation/review
- Code search
- Workflow triggers
- Release management

### 10. Context7 - Documentation Retrieval

**Purpose**: Up-to-date library and framework documentation

**Docker Configuration**:
```dockerfile
FROM node:20-alpine
RUN npm install -g context7-mcp
WORKDIR /app
ENV CACHE_TTL=3600
ENV MAX_DOCS_SIZE=50000
CMD ["context7-mcp"]
```

**Key Features**:
- Library resolution
- Version-specific docs
- Code examples
- API references

### 11. Morphllm Fast Apply - Code Editing

**Purpose**: Fast, accurate code modifications

**Docker Configuration**:
```dockerfile
FROM node:20-alpine
RUN npm install -g morphllm-fast-apply-mcp
ENV MORPHLLM_MODEL=gpt-4-turbo
ENV DRY_RUN_DEFAULT=false
CMD ["morphllm-fast-apply-mcp"]
```

**Key Features**:
- Minimal diff generation
- Multi-file edits
- Dry run capability
- Undo support

### 12. Exa - Web Search & Research

**Purpose**: AI-powered web research using official Exa API for high-quality development resources

**Docker Configuration**:
```dockerfile
FROM python:3.11-slim
RUN pip install exa-py>=1.0.0 fastmcp>=0.1.0 uvicorn[standard]>=0.30.0
WORKDIR /app
COPY exa_server.py .
ENV EXA_API_KEY=${EXA_API_KEY}
ENV MCP_SERVER_PORT=3008
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
  CMD curl -f http://localhost:3008/health || exit 1
CMD ["python", "exa_server.py"]
```

**Implementation**: Custom FastMCP server using official `exa-py` client

**Key Features**:
- **Neural Search**: AI-powered query processing with autoprompt
- **Content Extraction**: Full webpage content retrieval
- **Similar Discovery**: Find related websites and resources
- **Date Filtering**: Search by publication date ranges
- **Domain Control**: Include/exclude specific domains
- **Health Monitoring**: Built-in health checks for Docker

**Available Tools**:
- `search_web()` - AI-powered web search with autoprompt optimization
- `search_and_contents()` - Combined search + content retrieval
- `get_contents()` - Extract content from specific URLs
- `find_similar()` - Discover similar websites

**ADHD Optimizations**:
- Autoprompt feature reduces cognitive load for query formulation
- Structured JSON responses with clear categorization
- Error handling prevents workflow interruption
- Health monitoring ensures service reliability

## Supporting Services

### Calendar-Sync Service

**Purpose**: Bidirectional calendar synchronization

**Technology**: Python + caldav library

**Features**:
- iCal/CalDAV support
- Google Calendar API
- Outlook integration
- Task ↔ Event mapping
- Time block detection
- Conflict resolution

### Notification Service

**Purpose**: ADHD-friendly notifications

**Technology**: Python + terminal-notifier (macOS)

**Features**:
- Terminal notifications (tmux)
- macOS native notifications
- Progressive escalation
- Context-aware styling
- Sound profiles
- Visual indicators

### Time-Awareness Service

**Purpose**: Gentle time tracking without anxiety

**Technology**: Python + ML predictions

**Features**:
- Relative time display
- Progress visualization
- Break reminders
- Energy level tracking
- Deadline prevention
- Historical analysis

## MetaMCP Orchestrator

**Purpose**: Central gateway for role-based tool loading

**Architecture**:
```python
class MetaMCPOrchestrator:
    def __init__(self):
        self.active_servers = {}
        self.token_budget = 10000
        self.current_role = None

    async def load_role(self, role_name: str):
        """Dynamically load tools for role"""
        # Unload current tools
        await self.unload_all()

        # Load role-specific tools
        role_config = self.roles[role_name]
        for server, tools in role_config['tools'].items():
            await self.load_server(server, tools)

        # Track token usage
        self.update_token_count()
```

**Role Configurations**:
```yaml
roles:
  researcher:
    max_tokens: 8000
    servers:
      - exa: [search]
      - context7: [get_docs]
      - mas-sequential: [think]

  implementer:
    max_tokens: 10000
    servers:
      - morphllm: [edit_file]
      - claude-context: [search_code]
      - conport: [update_progress]

  reviewer:
    max_tokens: 9000
    servers:
      - zen: [codereview, consensus]
      - github: [create_review]
      - conport: [log_decision]
```

## Network Architecture

```yaml
networks:
  dopemux-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

services:
  # Each service connects to dopemux-net
  # Internal communication via service names
  # External access via published ports
```

## Volume Management

```yaml
volumes:
  # Persistent data
  postgres_data:
  redis_data:
  milvus_data:

  # MCP server data
  conport_data:
  openmemory_data:
  leantime_data:

  # Workspace
  workspace:
    driver: local
    driver_opts:
      type: none
      device: ${PWD}
      o: bind
```

## Environment Variables

```bash
# API Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
EXA_API_KEY=
GITHUB_TOKEN=

# Database
POSTGRES_PASSWORD=
REDIS_PASSWORD=

# Calendar
CALDAV_URL=
CALDAV_USERNAME=
CALDAV_PASSWORD=

# Notifications
NOTIFICATION_STYLE=adhd_friendly
NOTIFICATION_SOUND=gentle

# ADHD Settings
CHECKPOINT_INTERVAL=25m
BREAK_DURATION=5m
HYPERFOCUS_MAX=4h
```

## Health Checks

Each service includes health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Monitoring & Telemetry

### Metrics Collection

```yaml
prometheus:
  image: prom/prometheus
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
  volumes:
    - grafana_data:/var/lib/grafana
```

### Key Metrics

- Token usage per role
- Context switch frequency
- Task completion rate
- Focus session duration
- Tool usage patterns
- Response times
- Error rates

## Security Considerations

1. **API Key Management**: Use Docker secrets
2. **Network Isolation**: Internal network for MCP servers
3. **Data Encryption**: TLS for external connections
4. **Access Control**: Role-based permissions
5. **Audit Logging**: Track all operations

## Performance Optimization

1. **Lazy Loading**: Load tools only when needed
2. **Caching**: Redis for frequent queries
3. **Connection Pooling**: Reuse database connections
4. **Batch Operations**: Group similar requests
5. **Async Processing**: Non-blocking operations

## Disaster Recovery

1. **Automated Backups**: Daily PostgreSQL dumps
2. **Session Recovery**: Redis persistence
3. **Context Preservation**: ConPort exports
4. **Configuration Backup**: Git-tracked configs
5. **Quick Restore**: Docker compose rebuild

---

*Each server is designed to work independently but achieves maximum effectiveness when orchestrated together through the MetaMCP gateway.*