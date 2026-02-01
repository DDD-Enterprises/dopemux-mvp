# Dopemux Development Guide

Dopemux is an ADHD-optimized development platform that wraps AI assistants with cognitive accommodations, multi-workspace support, and a persistent knowledge graph (ConPort). It features a 64-agent distributed system with tmux-based UI, statusline awareness, and adaptive ritual scripts.

> **This guide consolidates information from**: `.claude/claude.md`, `src/.claude/claude.md`, `services/.claude/claude.md`, `docker/.claude/claude.md`, and project documentation.

## Build, Test, and Lint Commands

### Installation
```bash
make install-dev              # Install with dev dependencies
pip install -e .[dev]         # Alternative install method
```

### Testing
```bash
make test                     # Run all tests
make test-unit                # Unit tests only (-m "not integration")
make test-integration         # Integration tests only (-m integration)
make test-fast                # Skip slow tests (-m "not slow")
make test-coverage            # Generate coverage report (htmlcov/)
pytest -v                     # Verbose output
pytest path/to/test_file.py::test_function  # Run single test
```

**Test markers**: `slow`, `integration`, `unit`, `adhd`, `claude`, `config`, `asyncio`, `database`, `performance`

### Code Quality
```bash
make format                   # Format with black + isort
make lint                     # Run flake8
make type-check               # Run mypy
make quality                  # Run lint + type-check
make pre-commit               # Run all checks before committing
```

**Code style**: Black (line-length=88), isort (profile="black"), mypy with strict typing

### Service Management
```bash
# DopeconBridge (central coordination layer)
make bridge-status            # Check if bridge is running
make bridge-up                # Start bridge container
make bridge-down              # Stop bridge
make bridge-logs              # Tail logs
make bridge-validate          # Run integration validation
make bridge-client-test       # Run bridge client tests

# Docker Services
docker-compose -f docker-compose.unified.yml up -d    # Core stack
docker-compose -f docker-compose.master.yml up -d     # Full stack with all MCP servers
```

## Architecture Overview

### Three-Plane Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    PM Plane (Leantime)                  │
│                 Project Management Tasks                 │
└─────────────────────────────────────────────────────────┘
                             ▲
                             │
┌─────────────────────────────────────────────────────────┐
│                   DopeconBridge (port 3016)             │
│           Central coordination and event routing         │
└─────────────────────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Cognitive Plane        │  │   Coordination Plane     │
│   (ADHD services)        │  │   (Task Orchestrator)    │
│   - adhd-engine          │  │   - task-orchestrator    │
│   - voice-commands       │  │   - genetic-agent        │
│   - serena (search)      │  │   - workspace-watcher    │
│   - dddpg (graph)        │  │   - session-intelligence │
└──────────────────────────┘  └──────────────────────────┘
```

### DopeconBridge - The Central Nervous System
**DopeconBridge** is the **single integration point** for all 19+ services to:
- Access the ConPort knowledge graph (persistent memory across sessions)
- Publish/subscribe to events via Redis streams
- Route requests between PM and Cognitive planes

**Always use DopeconBridge** instead of direct ConPort access:
```python
from services.shared.dopecon_bridge_client import AsyncDopeconBridgeClient

client = AsyncDopeconBridgeClient.from_env()
await client.publish_event(event_type="task.completed", data={...}, source="my-service")
decisions = await client.recent_decisions(limit=10)
```

**Bridge adapters** live in each service directory (e.g., `services/adhd_engine/bridge_integration.py`)

### ConPort Knowledge Graph
ConPort is the persistent memory layer using PostgreSQL with AGE extension (Apache AGE for graph queries). It stores:
- Decisions and rationale
- Session context and continuity
- Cross-workspace knowledge
- Custom service data

**Never write to ConPort directly** - always go through DopeconBridge.

### Multi-Workspace Support
Each workspace has isolated:
- Cognitive state (energy, attention, breaks)
- Knowledge graph entries
- Session history

```bash
export DEFAULT_WORKSPACE_PATH=~/code/my-project
dopemux --workspace ~/code/another-project init
```

Workspace paths are detected from `cwd` or explicit `--workspace` flag.

## Key Conventions

### Service Communication Protocol
- **JSON-RPC 2.0** for all inter-service calls
- **Redis streams** for event pub/sub (via DopeconBridge)
- **REST/HTTP** for external integrations (Leantime, MCP servers)

### Error Handling Pattern
```python
from dopemux.error_handling import DopemuxError, handle_errors

@handle_errors
async def my_function():
    # Errors automatically logged and wrapped
    raise DopemuxError("Friendly error message", context={...})
```

All exceptions inherit from `DopemuxError` in `src/core/exceptions.py`.

### ADHD-Optimized Patterns
**Consent-first interactions**: Always prompt before interrupting focus
```python
# Good
if user_consents_to_notification():
    show_break_suggestion()

# Bad - immediate interruption
show_break_suggestion()
```

**Minimal cognitive load**: Use rich/textual for terminal UI, not raw print statements
```python
from rich.console import Console
console = Console()
console.print("[green]Task completed[/green]")
```

**Statusline awareness**: Update tmux statusline via `src/dopemux/tmux/statusline.py`, not direct tmux commands

**25-minute focus sessions**: Structure work around ADHD-optimized Pomodoro cycles
- Default to short feedback loops (sandbox, tests) before long-running tasks
- Maintain pane hygiene - close idle panes to reduce visual clutter
- Use color-coded monitors as high-level dashboard
- Note active work when switching contexts for quick resume

**Progressive disclosure**: Essential information first, details on-demand
- Keep functions small and single-purpose
- Use clear, self-documenting names
- Build features incrementally with working states
- Document non-obvious business logic inline

### Testing Conventions
- **Fixtures** in `tests/conftest.py` provide mocked services, temp dirs, and aiohttp stubs
- **Integration tests** require Docker services running (`make bridge-up`)
- **Async tests** use `@pytest.mark.asyncio` marker
- **Coverage requirement**: 80% minimum (`--cov-fail-under=80`)

### File Organization
```
src/
├── dopemux/           # Core platform code
│   ├── adhd/          # ADHD accommodations
│   ├── claude/        # Claude Code integration
│   ├── tmux/          # Terminal UI
│   └── cli/           # CLI commands
├── conport/           # Knowledge graph server
├── integrations/      # Bridge clients, sync managers
└── services/          # Microservices (not in src/, at repo root)
```

**Services** live at repo root under `services/` directory, not in `src/`.

### Environment Variables
Set these for full functionality:
```bash
# Core
DEFAULT_WORKSPACE_PATH=~/code/my-project
DOPECON_BRIDGE_URL=http://localhost:3016
DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane

# API Keys (for full stack)
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-v1-...
CONTEXT7_API_KEY=...
AGE_PASSWORD=...  # PostgreSQL password
```

Use `.env.example` as template; the installer creates `.env` automatically.

### Branding and Voice
Dopemux has a **distinctive brand voice**: kink-coded, consent-first, playful but precise. Examples:
- Statusline labels: `🧠` (brain), `⚡` (energy), `👁️` (attention), `☕` (breaks)
- CLI output: "Luxury filth plus lab precision"
- Logs: "Logged. Hydrate."

**Follow existing tone** in docs and UI text (see README.md for examples).

### Git Workflow
- **Main branch**: `main` (protected)
- **Feature branches**: Use `git worktree` - Dopemux has built-in worktree manager
- **Commits**: Conventional commits preferred (`feat:`, `fix:`, `docs:`)
- **Pre-commit hooks**: Run `make pre-commit` before pushing

### Docker Compose Stacks
- **unified** (`docker-compose.unified.yml`): Core services only (Postgres, Redis, Qdrant, ConPort, ADHD Engine, Task Orchestrator)
- **master** (`docker-compose.master.yml`): Full stack with all 12 MCP servers, DopeconBridge, coordination plane

Networks: `mcp-network`, `dopemux-unified-network`, `leantime-net` (created by installer)

### MCP Servers
MCP (Model Context Protocol) servers provide tool integrations. Key servers:
- **conport-mcp**: ConPort knowledge graph access (via DopeconBridge)
- **zen-mcp**: Zen meditation/focus tracking
- **context7**: Context management and retrieval
- **litellm**: LLM proxy/router

MCP configs live in `docker/mcp-servers/*/` with individual Dockerfiles and setup scripts.

### Statusline Implementation
The tmux statusline is **dynamically generated** by `src/dopemux/tmux/statusline.py`:
- Reads cognitive state from ADHD Engine API
- Displays workspace, git branch, energy/attention states, token usage
- Updates every 5 seconds via tmux `status-interval`

**Never hardcode statusline** - always use the generator.

### TMUX Orchestrator Pane Layout
```
┌ monitor:worktree ┬ monitor:logs ┬ monitor:metrics ┐
├────────────── orchestrator:control ───────┬ sandbox:shell ┤
└────────────── agent:primary ──────────────┴ (optional agent:secondary) ┘
```

**Colors**: Monitors use muted Gruvbox tones, orchestrator is deep charcoal, sandbox is magenta, agents are green.

**Pane Commands**:
- List panes: `dopemux tmux list`
- Capture history: `dopemux tmux capture agent:primary --lines 200`
- Send commands: `dopemux tmux send sandbox:shell "pytest -q\n"`
- Close pane: `dopemux tmux close --pane agent:secondary`
- Launch agent: `dopemux start --no-recovery --prompt .claude/agents/builder.md`

**Sandbox pane**: Use `$DOPEMUX_SANDBOX_PANE` for pane ID. All orchestrator processes inherit `DOPEMUX_DEFAULT_LITELLM=1` for OpenRouter routing.

### Package Structure
Python package is built from `src/` using setuptools:
```toml
[tool.setuptools.packages.find]
where = ["src"]
```

Entry point: `dopemux` command → `src/dopemux/cli.py:main()`

### Deprecation and Migration
Services in `services/*/archived/` are deprecated. Check `UNFINISHED_WORK.md` for migration status.

**Genetic Agent** is experimental - expect API changes.

## ADHD Engine Services

Dopemux Ultra UI provides 9+ ADHD-optimized microservices for cognitive accommodations:

### Core ADHD Engine (port 8080)
**6 API Endpoints**:
- `/api/v1/assess-task` - Task complexity assessment (0.0-1.0 scoring)
- `/api/v1/user-profile` - User ADHD profile management
- `/api/v1/energy-level` - Current energy state tracking
- `/api/v1/attention-state` - Real-time attention monitoring
- `/api/v1/cognitive-load` - Cognitive load measurement
- `/api/v1/break-recommendation` - Intelligent break suggestions

**6 Background Monitors**:
- Energy level tracking
- Attention state monitoring
- Cognitive load assessment
- Break suggestion engine (25-minute sessions)
- Hyperfocus detection
- Context switching tracker

**Health check**: `curl http://localhost:8080/health`

### Supporting Services
- **ADHD Dashboard** (port 8097): REST API for metrics visualization (`/api/metrics`, `/api/adhd-state`, `/api/sessions/today`, `/api/analytics/trends`)
- **ADHD Notifier**: Intelligent notifications (terminal, voice, system)
- **Break Suggester**: Proactive break suggestions using cognitive load patterns
- **Energy Trends**: Daily energy pattern analysis
- **Context Switch Tracker**: Monitor and optimize context switching
- **Complexity Coordinator**: Centralized code complexity assessments (0.0-1.0 scoring for ADHD-safe reading)
- **Workspace Watcher**: Monitor workspace changes and activity
- **Activity Capture**: Real-time activity pattern analysis

### LLM Integration with ADHD Services
**Before providing complex assistance**:
1. Query ADHD Dashboard APIs to check energy/attention state
2. Check energy levels to adjust response complexity
3. Use complexity scoring before recommending deep code dives
4. Respect break recommendations from the engine

**Communication style**:
- Use encouraging, non-judgmental tone
- Provide clear, actionable next steps
- Use visual indicators: ✅ ❌ ⚠️ 💡 🎯
- Essential info upfront, details on-demand

### Integration with ConPort
All ADHD services integrate with ConPort knowledge graph - decisions and patterns are automatically logged, session context preserved across work sessions.

## MCP Tools Available

### Desktop Commander MCP (port 3012)
**Purpose**: Desktop automation for ADHD-optimized workflows
**Status**: ✅ Fully operational with automatic X11 setup

**Tools**:
- `screenshot`: Capture desktop state for visual documentation
- `window_list`: List all open windows for workspace awareness
- `focus_window`: Auto-focus specific windows (eliminates manual switching)
- `type_text`: Type text via automation for repetitive tasks

**ADHD integration**: Automatic window focus after code navigation (Serena → Desktop Commander), visual context preservation, sub-2-second context switching

**Example workflow**:
```python
mcp__dope-context__search_code(query="authentication")
mcp__serena-v2__goto_definition(file_path="auth.py", line=42)
mcp__desktop-commander__focus_window(title="VS Code")  # Auto-focus!

# Visual decision logging
mcp__desktop-commander__screenshot(filename="/tmp/arch.png")
mcp__conport__log_decision(summary="Architecture approved", implementation_details="/tmp/arch.png")
```

### Other MCP Servers
- **conport-mcp**: ConPort knowledge graph access (via DopeconBridge)
- **zen-mcp**: Zen meditation/focus tracking
- **context7**: Context management and retrieval
- **litellm**: LLM proxy/router
- **dope-context**: Semantic search and autonomous indexing
- **serena-v2**: Code navigation and decision search

All MCP configs in `docker/mcp-servers/*/` with individual setup scripts.

## Python Development Standards

### Type Safety and Validation
```python
# Mandatory type hints for public interfaces
from pydantic import BaseModel
from typing import Optional

class CreateTaskRequest(BaseModel):
    """Pydantic models for all data validation."""
    title: str
    description: Optional[str] = None
    complexity: float  # 0.0-1.0
    energy_required: str  # "low", "medium", "high"

async def create_task(request: CreateTaskRequest) -> TaskResponse:
    """Type hints required for all public functions."""
    pass
```

### FastAPI Patterns
```python
from fastapi import FastAPI, HTTPException, Depends

@router.post("/endpoint", response_model=ResponseModel)
async def create_resource(
    data: CreateModel,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> ResponseModel:
    """Clear, specific docstring describing endpoint purpose."""
    try:
        result = await service.create_resource(data, current_user.id)
        return ResponseModel.from_domain(result)
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Service Lifecycle Management
```python
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle with proper startup/shutdown."""
    logger.info("🚀 Starting service")
    await initialize_dependencies()
    yield
    logger.info("🛑 Shutting down service")
    await cleanup_dependencies()

app = FastAPI(
    title="Service Name",
    description="Clear description",
    version="1.0.0",
    lifespan=lifespan
)
```

### Error Handling Hierarchy
```python
# Custom exception hierarchy in src/core/exceptions.py
class DopemuxError(Exception):
    """Base exception for all Dopemux errors."""
    pass

class ValidationError(DopemuxError):
    """Validation-specific errors with clear messages."""
    pass

class ServiceUnavailableError(DopemuxError):
    """Service connectivity errors."""
    pass
```

### Structured Logging
```python
import logging

# Configure at service startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use structured logging with context
logger.info("Task created", extra={"task_id": task.id, "user_id": user.id})
```

## Service Development Standards

### Service Structure Template
Every service in `services/` should follow this pattern:

```python
# services/[service-name]/main.py
"""
Service: [Service Name]
Purpose: [Clear description of service responsibility]
Dependencies: [List of required external services]
Health: /health endpoint for monitoring
"""
```

### Health Check Pattern
```python
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str
    version: str
    dependencies: dict[str, str]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Standard health check for all services."""
    try:
        dependency_status = await check_dependencies()
        return HealthResponse(
            service="service-name",
            version="1.0.0",
            dependencies=dependency_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
```

### Service Design Principles
- **Single Responsibility**: Each service handles one specific domain
- **Clear Boundaries**: Well-defined interfaces and communication patterns
- **Autonomous Operation**: Services can function independently when possible
- **ADHD-Friendly**: Predictable behavior, clear error handling, verbose logging

## Docker and Deployment

### Multi-Stage Dockerfile Pattern
```dockerfile
# Multi-stage build for Python services
FROM python:3.11-slim as base

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

WORKDIR /app

# Development stage
FROM base as development
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY --chown=app:app . .
USER app
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0"]

# Production stage
FROM base as production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
USER app

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

### ADHD-Optimized Container Philosophy
- **Clear Build Process**: Verbose output with progress indicators
- **Fast Iteration**: Quick rebuilds for development workflow
- **Error Visibility**: Clear error messages and debugging info
- **Consistent Environments**: Identical dev, staging, and production setups

## LLM Routing and Provider Strategy

### No Anthropic MAX Plan - Use LiteLLM/OpenRouter
All `dopemux start` processes run with `DOPEMUX_DEFAULT_LITELLM=1`, automatically routing through the local LiteLLM proxy.

**LiteLLM Configuration** (`litellm.config.yaml`):
- Claude Sonnet/Haiku/Opus clones via OpenRouter
- DeepSeek Chat/Coder
- xAI Grok Code Fast
- OpenAI GPT-4o/4o-mini via OpenRouter

**Manual API calls**: Use `openrouter/<provider>/<model>` endpoints with `OPENROUTER_API_KEY`.

**Required env vars**:
- `OPENROUTER_API_KEY` (required)
- `XAI_API_KEY` (optional but recommended)
- `OPENAI_API_KEY` (optional)

## Frequently Used Services & Patterns

### DopeconBridge Client Pattern
**Every service** uses the DopeconBridge client to access ConPort. Standard pattern:

```python
from services.shared.dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

class MyServiceAdapter:
    """DopeconBridge adapter for MyService"""
    
    def __init__(self, workspace_id: str, base_url: str = None):
        self.workspace_id = workspace_id
        
        config = DopeconBridgeConfig.from_env()
        if base_url:
            config = DopeconBridgeConfig(
                base_url=base_url,
                token=config.token,
                source_plane="cognitive_plane",  # or "pm_plane"
                timeout=config.timeout,
            )
        
        self.client = AsyncDopeconBridgeClient(config=config)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
```

**Key methods**:
- `create_progress_entry()` - Create tasks/decisions
- `publish_event()` - Publish events to Redis streams
- `save_custom_data()` / `get_custom_data()` - Service-specific data
- `recent_decisions()` - Query recent decisions
- `search_decisions()` - Search by keywords

### Multi-Workspace Resolution Pattern
Use `services/shared/workspace_utils.py` for consistent workspace handling:

```python
from services.shared.workspace_utils import resolve_workspaces

def my_function(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Multi-workspace aware function.
    
    Supports:
    - Single workspace (backward compatible)
    - Multiple workspaces (new)
    - Environment variable (DOPE_WORKSPACES)
    - Auto-detect from cwd
    """
    workspaces = resolve_workspaces(
        workspace_path=workspace_path,
        workspace_paths=workspace_paths,
        fallback_to_current=True,
        env_var_name="DOPE_WORKSPACES"
    )
    
    results = []
    for workspace in workspaces:
        # Process each workspace
        result = process_workspace(workspace)
        results.append(result)
    
    return results
```

**Priority order**: `workspace_paths` param → `workspace_path` param → `DOPE_WORKSPACES` env → current directory

### ADHD Engine API Client Pattern
Query ADHD state before complex operations:

```python
import aiohttp

async def check_adhd_state() -> Dict[str, Any]:
    """Query ADHD Engine for current cognitive state"""
    async with aiohttp.ClientSession() as session:
        # Get energy level
        async with session.get("http://localhost:8080/api/v1/energy-level") as resp:
            energy = await resp.json()
        
        # Get attention state
        async with session.get("http://localhost:8080/api/v1/attention-state") as resp:
            attention = await resp.json()
        
        # Get break recommendation
        async with session.get("http://localhost:8080/api/v1/break-recommendation") as resp:
            break_rec = await resp.json()
    
    return {
        "energy": energy.get("level"),  # "high", "medium", "low"
        "attention": attention.get("state"),  # "focused", "distracted", etc.
        "needs_break": break_rec.get("recommend_break", False),
    }

# Adjust behavior based on state
state = await check_adhd_state()
if state["energy"] == "low":
    # Provide simpler, more focused assistance
    return simplified_response()
elif state["needs_break"]:
    # Suggest taking a break first
    return break_suggestion()
```

### Service Bridge Adapter Pattern
Every service in `services/*/` should have a `bridge_adapter.py` or `bridge_integration.py`:

```python
# services/my-service/bridge_adapter.py
"""MyService DopeconBridge Adapter"""

from typing import Dict, Any
import logging
from services.shared.dopecon_bridge_client import AsyncDopeconBridgeClient

logger = logging.getLogger(__name__)

class MyServiceBridgeAdapter:
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.client = AsyncDopeconBridgeClient.from_env()
        logger.info(f"✅ MyService DopeconBridge adapter initialized")
    
    async def do_something(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform operation via DopeconBridge"""
        # Create decision or progress entry
        result = await self.client.create_progress_entry(
            description=f"MyService: {data['action']}",
            status="COMPLETED",
            metadata={"source": "my-service", **data},
            workspace_id=self.workspace_id,
        )
        
        # Publish event
        await self.client.publish_event(
            event_type="myservice.action.completed",
            data=data,
            source="my-service",
        )
        
        return result
```

**Naming convention**: `{ServiceName}BridgeAdapter` class in `services/{service-name}/bridge_adapter.py`

## Naming Conventions

### Service Names
- **Hyphenated lowercase**: `adhd-engine`, `task-orchestrator`, `dopemux-gpt-researcher`
- **Docker container names**: `dopemux-{service}` (e.g., `dopemux-postgres-age`)
- **Directory names**: `services/{service-name}/` (hyphenated)

### Python Modules and Classes
- **Modules**: `snake_case` (e.g., `bridge_adapter.py`, `workspace_utils.py`)
- **Classes**: `PascalCase` (e.g., `DopeconBridgeClient`, `ADHDAccommodationEngine`)
- **Functions**: `snake_case` (e.g., `resolve_workspaces`, `create_task`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_WORKSPACE_PATH`, `PORT_BASE`)

### API Endpoints
- **REST**: `/api/v1/{resource}` (e.g., `/api/v1/assess-task`, `/api/v1/energy-level`)
- **Health checks**: `/health` (always at root)
- **Metrics**: `/metrics` (Prometheus format)

### Environment Variables
- **Service-specific**: `{SERVICE}_API_KEY`, `{SERVICE}_URL` (e.g., `ANTHROPIC_API_KEY`, `LEANTIME_URL`)
- **Workspace-related**: `DEFAULT_WORKSPACE_PATH`, `WORKSPACE_PATHS`, `ENABLE_WORKSPACE_ISOLATION`
- **DopeconBridge**: `DOPECON_BRIDGE_URL`, `DOPECON_BRIDGE_SOURCE_PLANE`
- **Port convention**: `PORT_BASE=3000`, services use `PORT_BASE + offset` (e.g., bridge at 3016)

### File Organization
- **Adapters**: `services/{service}/bridge_adapter.py` or `{service}/adapters/bridge_adapter.py`
- **Main entry**: `services/{service}/main.py` (FastAPI app)
- **Config**: `services/{service}/config.py` (Pydantic settings)
- **Tests**: `tests/{category}/test_{service}.py`
- **Shared code**: `services/shared/{utility}.py` (e.g., `workspace_utils.py`, `dopecon_bridge_client.py`)

### Git Conventions
- **Branches**: `feature/{description}`, `fix/{description}`, `refactor/{description}`
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
- **Worktrees**: Use `dopemux` worktree commands, not raw `git worktree`

### Testing Conventions
- **Test files**: `test_{module}.py`
- **Test classes**: `Test{Feature}` (e.g., `TestBridgeAdapter`)
- **Test methods**: `test_{behavior}` (e.g., `test_create_task_via_bridge`)
- **Fixtures**: Defined in `conftest.py`, use descriptive names (e.g., `bridge_client`, `temp_workspace`)
- **Markers**: Apply relevant markers (`@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.adhd`)

## Common Development Workflows

### Workflow 1: Daily Startup
```bash
# 1. Start with DOPE layout (recommended)
dopemux dope --theme muted

# 2. Check service health
make bridge-status
curl http://localhost:8080/health  # ADHD Engine
curl http://localhost:3016/health  # DopeconBridge

# 3. Check your workspace context
dopemux query decisions --workspace ~/code/my-project --limit 5
dopemux tmux capture monitor:metrics --lines 50
```

### Workflow 2: Adding a New Feature
```bash
# 1. Create feature branch using dopemux worktree manager
dopemux worktree create feature/my-feature

# 2. Run tests to establish baseline
make test-coverage

# 3. Make changes, test incrementally
pytest tests/path/to/test_file.py::test_function -vv

# 4. Format and lint
make format
make quality

# 5. Commit with conventional commit
git commit -m "feat: add new feature with ADHD optimization"

# 6. Log decision to ConPort via DopeconBridge
# (Usually done automatically by services, but can be manual)
curl -X POST http://localhost:3016/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Implemented feature X",
    "rationale": "Improves cognitive load for Y",
    "implementation_details": "Used pattern Z"
  }'
```

### Workflow 3: Debugging Service Integration
```bash
# 1. Check DopeconBridge connectivity
make bridge-validate

# 2. Check service logs
make bridge-logs
docker logs -f dopemux-adhd-engine

# 3. Test bridge client manually
pytest tests/shared/test_dopecon_bridge_client.py -vv

# 4. Verify events published to Redis
docker exec -it dopemux-redis redis-cli
> XREAD COUNT 10 STREAMS dopemux:events 0

# 5. Check health endpoints
curl http://localhost:3016/health
curl http://localhost:3016/stats | jq
```

### Workflow 4: Multi-Workspace Development
```bash
# 1. Set up workspaces
export DEFAULT_WORKSPACE_PATH=~/code/dopemux-mvp
export WORKSPACE_PATHS=~/code/project1,~/code/project2

# 2. Query across workspaces
dopemux query decisions --workspaces ~/code/project1,~/code/project2

# 3. Work in specific workspace
cd ~/code/project1
dopemux --workspace $(pwd) init

# 4. Check workspace-specific state
curl "http://localhost:8080/api/v1/adhd-state?workspace_id=project1"

# 5. Switch workspace context in tmux
dopemux workspace switch ~/code/project2
```

### Workflow 5: Service Development
```bash
# 1. Create new service
mkdir -p services/my-service
cd services/my-service

# 2. Create service structure
cat > main.py << 'EOF'
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting my-service")
    yield
    print("🛑 Shutting down my-service")

app = FastAPI(title="My Service", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "my-service"}
EOF

# 3. Create bridge adapter
cat > bridge_adapter.py << 'EOF'
from services.shared.dopecon_bridge_client import AsyncDopeconBridgeClient

class MyServiceBridgeAdapter:
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.client = AsyncDopeconBridgeClient.from_env()
EOF

# 4. Add to docker-compose.master.yml
# 5. Add tests in tests/integration/
# 6. Update DOPECONBRIDGE_SERVICE_CATALOG.md
```

### Workflow 6: TMUX Orchestration
```bash
# From orchestrator pane:

# 1. Check pane layout
dopemux tmux list

# 2. Capture agent output
dopemux tmux capture agent:primary --lines 200

# 3. Send command to sandbox
dopemux tmux send sandbox:shell "pytest -v\n"

# 4. Launch agent with persona
dopemux start --no-recovery \
  --prompt .claude/agents/builder.md \
  --decision CONPORT_DECISION_ID

# 5. Monitor in real-time
dopemux tmux capture monitor:logs --lines 100 --follow

# 6. Clean up when done
dopemux tmux close --pane agent:secondary
```

## Common Patterns

### Adding a New Service
1. Create service directory: `services/my-service/`
2. Add `main.py` with FastAPI app and `/health` endpoint
3. Add `bridge_adapter.py` implementing DopeconBridge client
4. Add `config.py` with Pydantic settings
5. Add Dockerfile (use multi-stage pattern from `docker/.claude/claude.md`)
6. Add service to `docker-compose.master.yml` or `docker-compose.unified.yml`
7. Update `DOPECONBRIDGE_SERVICE_CATALOG.md`
8. Write integration test in `tests/integration/test_my_service.py`
9. Add service documentation in `services/my-service/README.md`

### Querying Recent Decisions
```python
client = AsyncDopeconBridgeClient.from_env()
decisions = await client.recent_decisions(limit=10, workspace_id="my-workspace")
for decision in decisions:
    print(decision["title"], decision["rationale"])
```

### Publishing Events
```python
await client.publish_event(
    event_type="task.completed",
    data={"task_id": "T-123", "duration_seconds": 300},
    source="my-service",
    stream="dopemux:events"  # Optional, defaults to dopemux:events
)
```

### Adding a TMUX Pane
Edit `src/dopemux/tmux/layout_templates.py`, add pane definition to appropriate layout, then update bootstrap logic in `src/dopemux/tmux/bootstrap.py`.

### TMUX Orchestrator Workflow Template
1. **Orient**: `dopemux tmux list`, skim monitor panes for errors
2. **Clarify request**: Decide which agent(s) to engage
3. **Prepare sandbox/agents**: Run tests in `sandbox:shell`, launch/reset agents
4. **Delegate**: Use `dopemux tmux send` to communicate instructions, monitor via `dopemux tmux capture`
5. **Consolidate results**: Reference captured logs in response
6. **Tidy up**: Close extra agents, stop sandbox jobs, log decisions to ConPort

### Running Installer Tests
```bash
INSTALLER_TEST_MODE=1 ./install.sh --quick  # Dry-run mode for CI
./test_installer_basic.sh                   # Actual installer test
```

## Documentation Structure
- `docs/94-architecture/`: System design, architecture decisions
- `docs/branding/`: Brand voice, visual identity
- `docs/06-research/`: Research notes on ADHD optimization, knowledge graphs
- Root-level `*_SUMMARY.md`, `*_COMPLETE.md`: Session logs (archival, not authoritative)

**Authoritative docs**: README.md, INSTALL.md, QUICK_REFERENCE.md, START_HERE_*.md

## Debugging Tips

### Service Not Starting
1. Check logs: `make bridge-logs` or `docker logs -f <container-name>`
2. Verify networks exist: `docker network ls | grep dopemux`
3. Check env vars: `docker exec <container> env | grep API_KEY`

### Tests Failing
1. Ensure Docker services running: `docker ps | grep dopemux`
2. Check coverage report: `open htmlcov/index.html`
3. Run single test verbosely: `pytest -vvs tests/path/to/test.py::test_name`

### Bridge Integration Issues
1. Validate bridge: `make bridge-validate`
2. Test health: `curl http://localhost:3016/health`
3. Check stats: `curl http://localhost:3016/stats | jq`
4. Run client tests: `make bridge-client-test`

### Statusline Not Updating
1. Check ADHD Engine: `curl http://localhost:8001/health`
2. Verify tmux session: `tmux list-sessions`
3. Check statusline script: `python src/dopemux/tmux/statusline.py --test`

## Code Quality Standards

### Complexity Management
- Keep cyclomatic complexity under 10 per function
- Docstrings for all public functions and classes
- Minimum 80% code coverage for business logic
- Profile critical paths and optimize for ADHD workflow efficiency

### Module Organization
- **Clear separation**: domain logic, API layer, infrastructure
- **Dependency injection**: Use FastAPI's dependency system for testability
- **Configuration**: Environment-based config with Pydantic settings
- **Small functions**: Break complex logic into focused, single-purpose functions

### Development Workflow Best Practices
- **Test-first**: Write tests before implementation for complex business logic
- **Frequent commits**: Small, focused commits with clear messages (conventional commits preferred: `feat:`, `fix:`, `docs:`)
- **Refactor regularly**: Keep code clean through continuous improvement
- **Document decisions**: Log implementation decisions in ConPort

## Agent Coordination Roles

### Developer Agent (Primary)
**When working in `src/`**:
- Focus on code quality and maintainability
- Ensure type safety and proper error handling
- Integrate with project-wide patterns and standards
- Log implementation decisions in ConPort

### Architect Agent (Consultation)
**For design decisions**:
- Review module boundaries and dependency directions
- Validate design patterns and architectural principles
- Ensure new code aligns with system architecture
- Guide refactoring efforts for better structure

## Quick Reference: Common Gotchas

### ❌ DON'T: Access ConPort Directly
```python
# BAD - bypasses authority boundaries
import psycopg2
conn = psycopg2.connect(postgres_dsn)
conn.execute("INSERT INTO decisions ...")
```

### ✅ DO: Use DopeconBridge
```python
# GOOD - respects two-plane architecture
from services.shared.dopecon_bridge_client import AsyncDopeconBridgeClient
client = AsyncDopeconBridgeClient.from_env()
await client.create_progress_entry(...)
```

### ❌ DON'T: Hardcode Workspace Paths
```python
# BAD - assumes single workspace
workspace = Path("~/code/dopemux-mvp")
```

### ✅ DO: Use resolve_workspaces
```python
# GOOD - multi-workspace aware
from services.shared.workspace_utils import resolve_workspaces
workspaces = resolve_workspaces(workspace_path=path)
for workspace in workspaces:
    process(workspace)
```

### ❌ DON'T: Print to stdout in Services
```python
# BAD - not structured, hard to debug
print("Task completed")
```

### ✅ DO: Use Structured Logging
```python
# GOOD - structured, filterable, has context
logger.info("Task completed", extra={"task_id": task.id, "duration": 5.2})
```

### ❌ DON'T: Skip Health Checks
```python
# BAD - no way to monitor service
app = FastAPI(title="My Service")
```

### ✅ DO: Implement Standard Health Endpoint
```python
# GOOD - standardized monitoring
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", service="my-service", version="1.0.0")
```

### ❌ DON'T: Ignore ADHD State
```python
# BAD - overwhelming when user is low energy
async def complex_analysis():
    # Return 500 lines of dense technical details
    return generate_massive_report()
```

### ✅ DO: Adapt to Cognitive State
```python
# GOOD - progressive disclosure based on energy
async def adaptive_analysis():
    state = await check_adhd_state()
    if state["energy"] == "low":
        return simplified_summary()
    elif state["attention"] == "distracted":
        return bullet_points_only()
    else:
        return detailed_analysis()
```

### ❌ DON'T: Use Generic Exception Handling
```python
# BAD - loses error context
try:
    result = await do_something()
except Exception:
    return {"error": "Something went wrong"}
```

### ✅ DO: Use Typed Exceptions
```python
# GOOD - clear error handling
from src.core.exceptions import DopemuxError, ServiceUnavailableError

try:
    result = await do_something()
except ServiceUnavailableError as e:
    logger.error(f"Service unavailable: {e}", extra={"service": "bridge"})
    raise HTTPException(status_code=503, detail=str(e))
except DopemuxError as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

## Additional Resources

### Documentation
- **Quick Start**: `dopemux dope --theme muted` (one-command full setup)
- **Service Catalog**: `DOPECONBRIDGE_SERVICE_CATALOG.md` (all 19+ services)
- **Multi-Workspace**: `START_HERE_MULTI_WORKSPACE.md`
- **Production Readiness**: `PRODUCTION_READINESS_SUMMARY.md`
- **Ultra UI MVP**: `docs/dopemux-ultra-ui-mvp-summary.md` - Complete feature overview
- **ADHD Engine**: `services/adhd_engine/README.md` - Service architecture and APIs
- **Dope Context**: `services/dope-context/README.md` - Semantic search and indexing
- **Orchestrator Workflow**: `docs/ORCHESTRATOR_WORKFLOW.md` - Deep dive into orchestration patterns
- **Security Testing**: `tests/security/README.md` - Security framework and guidelines
- **LiteLLM Config**: `litellm.config.yaml` - OpenRouter/LiteLLM provider map

### Context-Specific Guides
- **Root `.claude/claude.md`**: Orchestrator guide, pane layout, ADHD services, MCP tools
- **`src/.claude/claude.md`**: Python development standards, type safety, error handling
- **`services/.claude/claude.md`**: Service architecture, development standards, health patterns
- **`docker/.claude/claude.md`**: Container philosophy, multi-stage builds, deployment
