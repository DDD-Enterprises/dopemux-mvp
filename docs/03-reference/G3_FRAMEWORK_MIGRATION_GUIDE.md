---
id: g3-framework-migration
title: G3 Framework Migration Guide
type: reference
owner: architecture
date: 2026-01-31
status: active
tags:
- architecture
- cli
- migration
- g3-framework
last_review: '2026-01-31'
next_review: '2026-05-01'
author: '@hu3mann'
prelude: G3 Framework Migration Guide (reference) for dopemux documentation and developer
  workflows.
---
# G3 Framework Migration Guide

**Overview**: Complete guide for understanding and working with the G3 Framework CLI architecture recovered from the backup.

**Last Updated**: 2026-01-31
**Status**: Active
**Scope**: CLI architecture, module organization, client abstractions

---

## Table of Contents

1. [What is G3 Framework?](#what-is-g3-framework)
2. [Architectural Changes](#architectural-changes)
3. [Migration Paths](#migration-paths)
4. [Module Reference](#module-reference)
5. [Breaking Changes](#breaking-changes)
6. [Developer Guide](#developer-guide)
7. [Troubleshooting](#troubleshooting)

---

## What is G3 Framework?

**G3 Framework** is the third-generation CLI architecture for Dopemux, introducing:
- **Modular command structure** - Commands organized in logical groups
- **Client abstraction layer** - Unified interface for HTTP/MCP services
- **Health check system** - Comprehensive service health monitoring
- **Enhanced orchestrator** - Improved task coordination
- **Service registry** - Dynamic service discovery

### Key Benefits

✅ **Maintainability**: Clear separation of concerns, easier to extend
✅ **Testability**: Modular structure enables isolated testing
✅ **Discoverability**: Logical command grouping improves UX
✅ **Scalability**: Plugin-style architecture supports growth
✅ **Type Safety**: Enhanced type hints and validation

---

## Architectural Changes

### Before G3 (Legacy)

```
src/dopemux/
├── cli.py                 # 252KB monolithic CLI file
├── config.py             # Global configuration
├── tmux/                 # tmux utilities
└── [other modules]
```

**Characteristics**:
- Single massive `cli.py` file (~7,000 lines)
- Direct imports mixing concerns
- Tight coupling between commands
- Difficult to test in isolation

### After G3 (Current)

```
src/dopemux/
├── cli/                  # Modular CLI structure
│   ├── __init__.py       # CLI initialization
│   ├── main.py          # Application entry point
│   ├── registry.py      # Command registration system
│   └── commands/        # Command modules
│       ├── core.py      # Core commands (init, status, etc.)
│       ├── tmux.py      # tmux controller commands
│       ├── mcp.py       # MCP server management
│       ├── worktrees.py # Git worktree commands
│       ├── profile.py   # Profile management
│       ├── decisions.py # Decision logging
│       ├── extract.py   # Document extraction
│       └── trigger.py   # Hook triggers
├── cli_legacy.py        # Preserved legacy CLI for compatibility
├── clients/             # Service client abstractions
│   ├── _http.py         # Base HTTP client
│   ├── conport.py       # ConPort client factory
│   ├── conport_client.py # ConPort MCP client
│   ├── conport_http.py   # ConPort HTTP client
│   ├── conport_mcp.py    # ConPort MCP wrapper
│   ├── dopecon_bridge_client.py # DopeconBridge client
│   └── task_orchestrator_client.py # Task orchestrator client
├── health/              # Health check system
│   ├── checks.py        # Health check implementations
│   ├── errors.py        # Health-specific exceptions
│   ├── handlers.py      # Error handling utilities
│   └── models.py        # Health status models
├── orchestrator/        # Enhanced orchestrator
│   ├── engine.py        # Orchestration engine
│   ├── models.py        # Task and agent models
│   ├── query.py         # Task query interface
│   └── state.py         # State management
├── logging/             # Structured logging
│   ├── config.py        # Logging configuration
│   └── middleware.py    # Logging middleware
├── registry/            # Service registry
│   └── services.py      # Service discovery
└── config/              # Enhanced configuration
    └── manager.py       # Configuration management

src/core/                # Core infrastructure
├── config/              # Core configuration
│   └── claude_autoresponder.py
├── exceptions.py        # Core exceptions
└── monitoring.py        # Monitoring utilities
```

**Characteristics**:
- Modular command structure
- Clear separation of concerns
- Plugin-style architecture
- Testable in isolation
- Type-safe abstractions

---

## Migration Paths

### For Developers

#### 1. Importing CLI Components

**Before (Legacy)**:
```python
from dopemux.cli import cli, some_command
```

**After (G3)**:
```python
from dopemux.cli import cli, main
from dopemux.cli.commands.core import status_cmd
```

#### 2. Adding New Commands

**Before (Legacy)**:
```python
# Edit the massive cli.py file directly
@cli.command()
def my_command():
    pass
```

**After (G3)**:
```python
# Create new command module in cli/commands/
# File: src/dopemux/cli/commands/my_feature.py

import click

def register(cli):
    """Register my_feature commands with CLI."""

    @cli.command()
    def my_command():
        """My new command."""
        pass

# In cli/registry.py, add to registration:
from .commands import my_feature
my_feature.register(cli)
```

#### 3. Using Service Clients

**Before (Legacy)**:
```python
# Direct HTTP calls or MCP imports
import requests
response = requests.post("http://localhost:5432/api/...")
```

**After (G3)**:
```python
# Use abstracted clients
from dopemux.clients.conport import get_conport_client

client = get_conport_client()
result = client.log_decision(
    workspace_id="/path/to/workspace",
    summary="Decision summary",
    rationale="Why we decided this"
)
```

#### 4. Health Checks

**Before (Legacy)**:
```python
# Manual health checking
from dopemux.health import HealthChecker
checker = HealthChecker()
status = checker.check()
```

**After (G3)**:
```python
# Structured health system
from dopemux.health.checks import run_health_checks
from dopemux.health.models import HealthStatus

results = run_health_checks()
if results.status == HealthStatus.UNHEALTHY:
    # Handle unhealthy state
    pass
```

### For Tests

#### Updating Test Imports

**Problem**:
```python
# Old tests that fail
from core.config import Config  # ModuleNotFoundError
```

**Solution**:
```python
# Update to new structure
from dopemux.config.manager import ConfigManager

config = ConfigManager()
```

#### Test Fixture Updates

**Before**:
```python
@pytest.fixture
def health_checker():
    from dopemux.health import HealthChecker
    return HealthChecker()
```

**After**:
```python
@pytest.fixture
def health_checks():
    from dopemux.health.checks import run_health_checks
    return run_health_checks
```

---

## Module Reference

### CLI Command Modules

| Module | Commands | Purpose |
|--------|----------|---------|
| `commands/core.py` | `init`, `status`, `doctor`, `wire-conport` | Core Dopemux commands |
| `commands/tmux.py` | `tmux list`, `tmux send`, `tmux capture`, `tmux happy` | tmux controller |
| `commands/mcp.py` | `mcp start`, `mcp stop`, `mcp status`, `mcp logs` | MCP server management |
| `commands/worktrees.py` | `worktrees list`, `worktrees create`, `worktrees cleanup` | Git worktree management |
| `commands/profile.py` | `profile create`, `profile switch`, `profile list` | Multi-project profiles |
| `commands/decisions.py` | `decisions log`, `decisions list`, `decisions search` | Decision logging (ConPort) |
| `commands/extract.py` | `extract docs`, `extract code` | Document/code extraction |
| `commands/trigger.py` | `trigger precommit`, `trigger postmerge` | Git hook triggers |
| `commands/code.py` | `code analyze`, `code format` | Code analysis commands |

### Client Abstractions

| Client | Purpose | Protocol Support |
|--------|---------|-----------------|
| `conport.py` | ConPort service access | HTTP + MCP (auto-detects) |
| `conport_http.py` | ConPort HTTP client | HTTP only |
| `conport_mcp.py` | ConPort MCP client | MCP only |
| `dopecon_bridge_client.py` | DopeconBridge service | HTTP |
| `task_orchestrator_client.py` | Task orchestration | HTTP |
| `_http.py` | Base HTTP client | HTTP (base class) |

### Health Check System

| Module | Components | Purpose |
|--------|-----------|---------|
| `health/checks.py` | `DockerHealthCheck`, `MCPHealthCheck`, `ServiceHealthCheck` | Service health validation |
| `health/models.py` | `HealthStatus`, `HealthResult`, `HealthReport` | Health data models |
| `health/errors.py` | `HealthCheckError`, `ServiceUnavailable` | Health-specific exceptions |
| `health/handlers.py` | `handle_health_error()`, `log_health_status()` | Error handling utilities |

### Orchestrator Components

| Module | Components | Purpose |
|--------|-----------|---------|
| `orchestrator/engine.py` | `OrchestratorEngine` | Task orchestration engine |
| `orchestrator/models.py` | `OrchestrationTask`, `AgentType`, `TaskStatus` | Data models |
| `orchestrator/query.py` | `TaskQuery`, `get_tasks()`, `filter_tasks()` | Task querying |
| `orchestrator/state.py` | `StateManager`, `save_state()`, `load_state()` | State persistence |

---

## Breaking Changes

### Import Changes

| Old Import | New Import | Notes |
|------------|-----------|-------|
| `from dopemux.cli import cli` | `from dopemux.cli import cli` | ✅ No change (backwards compatible) |
| `from dopemux.health import HealthChecker` | `from dopemux.health.checks import run_health_checks` | ⚠️ Breaking - use new API |
| `from core.config import Config` | `from dopemux.config.manager import ConfigManager` | ⚠️ Breaking - different module |
| `from dopemux.cli import status_cmd` | `from dopemux.cli.commands.core import status_cmd` | ⚠️ Breaking - moved to submodule |

### API Changes

#### Health Checks

**Before**:
```python
checker = HealthChecker()
status = checker.check_all()
print(status.is_healthy)
```

**After**:
```python
from dopemux.health.checks import run_health_checks
from dopemux.health.models import HealthStatus

results = run_health_checks()
is_healthy = results.status == HealthStatus.HEALTHY
```

#### Configuration

**Before**:
```python
from core.config import Config
config = Config.load()
```

**After**:
```python
from dopemux.config.manager import ConfigManager
config = ConfigManager()
settings = config.load_settings()
```

### Removed Components

- ❌ `dopemux.health.HealthChecker` - Replaced with `health.checks.run_health_checks()`
- ❌ `core.config.Config` - Replaced with `dopemux.config.manager.ConfigManager`
- ❌ Direct CLI imports - Use `cli.commands.*` modules

---

## Developer Guide

### Adding a New Command

**Step 1**: Create command module
```python
# File: src/dopemux/cli/commands/my_feature.py
import click

def register(cli):
    """Register my_feature commands."""

    @cli.group()
    def my_feature():
        """My feature commands."""
        pass

    @my_feature.command()
    def do_something():
        """Do something useful."""
        click.echo("Doing something...")
```

**Step 2**: Register in registry
```python
# File: src/dopemux/cli/registry.py
def _register_feature_commands(cli):
    """Register feature commands."""
    from .commands import my_feature
    my_feature.register(cli)
```

**Step 3**: Add to registration list
```python
# In register_all():
_register_core_commands(cli)
_register_feature_commands(cli)  # Add this line
```

### Creating a Service Client

**Step 1**: Create client class
```python
# File: src/dopemux/clients/my_service_client.py
from ._http import BaseHTTPClient

class MyServiceClient(BaseHTTPClient):
    """Client for MyService API."""

    def __init__(self, base_url: str):
        super().__init__(base_url)

    def do_something(self, param: str) -> dict:
        """Call service endpoint."""
        return self.post("/api/v1/something", json={"param": param})
```

**Step 2**: Create factory function
```python
# File: src/dopemux/clients/my_service.py
from .my_service_client import MyServiceClient

def get_my_service_client() -> MyServiceClient:
    """Get configured MyService client."""
    from dopemux.config.manager import ConfigManager

    config = ConfigManager()
    base_url = config.get("MY_SERVICE_URL", "http://localhost:8080")

    return MyServiceClient(base_url)
```

**Step 3**: Export in `__init__.py`
```python
# File: src/dopemux/clients/__init__.py
from .my_service import get_my_service_client

__all__ = ["get_my_service_client"]
```

### Adding Health Checks

**Step 1**: Create health check class
```python
# File: src/dopemux/health/checks.py
class MyServiceHealthCheck:
    """Health check for MyService."""

    async def check(self) -> HealthResult:
        """Perform health check."""
        try:
            client = get_my_service_client()
            response = client.health()

            return HealthResult(
                status=HealthStatus.HEALTHY,
                message="MyService is operational",
                latency_ms=response.get("latency")
            )
        except Exception as e:
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                message=f"MyService check failed: {str(e)}"
            )
```

**Step 2**: Register in `run_health_checks()`
```python
def run_health_checks() -> HealthReport:
    """Run all health checks."""
    checks = [
        DockerHealthCheck(),
        MCPHealthCheck(),
        MyServiceHealthCheck(),  # Add your check
    ]

    results = []
    for check in checks:
        result = await check.check()
        results.append(result)

    return HealthReport(results=results)
```

---

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError: No module named 'core.config'

**Problem**: Test or script using old import path

**Solution**: Update imports
```python
# Old (broken)
from core.config import Config

# New (working)
from dopemux.config.manager import ConfigManager
```

#### 2. ImportError: cannot import name 'HealthChecker'

**Problem**: Using old health check API

**Solution**: Use new health system
```python
# Old (broken)
from dopemux.health import HealthChecker

# New (working)
from dopemux.health.checks import run_health_checks
```

#### 3. Command not found after adding new command

**Problem**: Forgot to register command in registry

**Solution**: Add registration call
```python
# In src/dopemux/cli/registry.py
def register_all(cli):
    _register_core_commands(cli)
    _register_my_new_commands(cli)  # Add this
```

#### 4. Tests fail with import errors

**Problem**: Test fixtures reference old module structure

**Solution**: Update test imports and fixtures
```python
# Update conftest.py or test file
@pytest.fixture
def config_manager():
    from dopemux.config.manager import ConfigManager
    return ConfigManager()
```

### Debug Checklist

- [ ] Verify imports use new module paths
- [ ] Check `cli/registry.py` for command registration
- [ ] Ensure client factories are properly configured
- [ ] Validate health checks are registered
- [ ] Update test fixtures for new structure
- [ ] Clear `__pycache__` directories if encountering weird import errors

---

## Additional Resources

- **CLI Reference**: `docs/03-reference/CLI_REFERENCE.md`
- **Client API Docs**: `docs/03-reference/CLIENT_API.md`
- **Health System**: `docs/03-reference/HEALTH_SYSTEM.md`
- **Orchestrator Guide**: `docs/03-reference/ORCHESTRATOR.md`

---

## Change Log

### 2026-01-31 - Initial G3 Framework Recovery
- Restored modular CLI architecture from backup
- Recovered client abstraction layer
- Restored health check system
- Recovered orchestrator enhancements
- Created migration guide

---

**Questions?** See `docs/02-how-to/` for specific how-to guides or ask in project discussions.
