---
id: DOPE_MEMORY_INTEGRATION
title: Dope Memory Integration
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-02'
last_review: '2026-03-02'
next_review: '2026-05-31'
prelude: Dope Memory Integration (explanation) for dopemux documentation and developer
  workflows.
---
# Dope-Memory Integration Guide

## Overview

This document explains how dope-memory, conport, serena, and dope-context services are now properly integrated into the Dopemux system and how agents should use them.

## Changes Made

### 1. Dope-Memory Service Startup

**Problem**: Dope-memory was not being started during `dopemux start` because:
- Missing `docker-compose.yml` file in `docker/mcp-servers/`
- Dope-memory not included in startup script
- Dope-memory not in MCP server configuration

**Solution**:
- Created `docker/mcp-servers/docker-compose.yml` with dope-memory service
- Updated `start-all-mcp-servers.sh` to start dope-memory
- Added dope-memory to health checks and service status
- Added dope-memory to `.claude.json` MCP server configuration

### 2. Service Configuration

#### Dope-Memory
- **Port**: 3020
- **Health Endpoint**: `/health`
- **MCP Endpoint**: `http://localhost:3020/mcp`
- **Tools Available**:
  - `memory_search`: Keyword + filters search
  - `memory_store`: Explicit manual entry
  - `memory_recap`: Session/today summary
  - `memory_mark_issue`: Flag entry as issue
  - `memory_link_resolution`: Link issue -> resolution
  - `memory_replay_session`: Chronological session entries

#### ConPort
- **Port**: 3004
- **Health Endpoint**: `/health`
- **MCP Endpoint**: `http://localhost:3004/mcp`
- **Purpose**: Project memory and decision tracking

#### Serena
- **Port**: 3006
- **Health Endpoint**: `/health`
- **MCP Endpoint**: `http://localhost:3006/sse`
- **Purpose**: ADHD-optimized code navigation and project memory

#### Dope-Context
- **Port**: 3010
- **Health Endpoint**: `/health`
- **MCP Endpoint**: `http://localhost:3010/mcp`
- **Purpose**: Semantic search and context management

## How Agents Should Use These Services

### 1. Dope-Memory Usage

Dope-memory provides temporal chronicle and working-context management:

```python
# Search memory
result = await mcp_call("dopemux-dope-memory", "memory_search", {
    "query": "implementation of feature X",
    "filters": {
        "category": "implementation",
        "time_range": "last_7_days"
    }
})

# Store explicit memory entry
await mcp_call("dopemux-dope-memory", "memory_store", {
    "entry_type": "decision",
    "content": "Decided to use approach Y for feature X",
    "tags": ["architecture", "feature-x"]
})

# Get session recap
recap = await mcp_call("dopemux-dope-memory", "memory_recap", {
    "time_range": "today"
})
```

### 2. ConPort Usage

ConPort provides project memory and decision tracking:

```python
# Log design decision
await mcp_call("dopemux-conport", "log_decision", {
    "decision": "Use Redis for caching layer",
    "rationale": "Better performance than SQLite for our use case",
    "tags": ["architecture", "performance"]
})

# Search decisions
decisions = await mcp_call("dopemux-conport", "search_decisions", {
    "query": "caching",
    "tags": ["architecture"]
})
```

### 3. Serena Usage

Serena provides ADHD-optimized code navigation:

```python
# Code navigation
result = await mcp_call("dopemux-serena", "code_nav", {
    "query": "find all usages of UserModel",
    "file_patterns": ["*.py"]
})

# Get project context
context = await mcp_call("dopemux-serena", "get_project_context", {})
```

### 4. Dope-Context Usage

Dope-Context provides semantic search:

```python
# Semantic search
results = await mcp_call("dopemux-claude-context", "semantic_search", {
    "query": "authentication implementation",
    "limit": 5
})

# Context-aware search
context_results = await mcp_call("dopemux-claude-context", "context_aware_search", {
    "query": "user session management",
    "context": "authentication system"
})
```

## Agent Configuration Example

Here's how to configure an agent to use these services:

```yaml
# In your agent configuration
services:
  memory:
    provider: "dopemux-dope-memory"
    tools: ["memory_search", "memory_store", "memory_recap"]

  decisions:
    provider: "dopemux-conport"
    tools: ["log_decision", "search_decisions"]

  code_nav:
    provider: "dopemux-serena"
    tools: ["code_nav", "get_project_context"]

  semantic_search:
    provider: "dopemux-claude-context"
    tools: ["semantic_search", "context_aware_search"]

# Task routing
task_routing:
  memory_operations: "dopemux-dope-memory"
  decision_logging: "dopemux-conport"
  code_analysis: "dopemux-serena"
  context_search: "dopemux-claude-context"
```

## Multi-Instance MCP Wiring (Deterministic Routing)

Dopemux now supports project-scoped MCP instances to prevent state contamination between different worktrees or projects. This is managed by the **Instance Resolver** and enforced by the **Phase 0 Discovery Gate**.

### 1. Instance Configuration

Project-specific endpoints are defined in `.dopemux/mcp.instances.toml`.

**Priority Order for Resolution**:
1.  **Repo Profile**: `.dopemux/mcp.instances.toml` (or specific profile via `--profile`)
2.  **Environment Variables**: `DOPMUX_CONPORT_URL`, `DOPMUX_SERENA_URL`, etc.
3.  **Global Fallback**: `~/.vibe/config.toml`

**Schema Example (`.dopemux/mcp.instances.toml`)**:
```toml
[project]
project_id = "my-project"
instance_profile = "default"

[mcp.conport]
url = "http://127.0.0.1:3004/mcp"
transport = "http"
required_tool_globs = ["conport_*"]
```

### 2. Auto-Provisioning (dopemux start)

When running `dopemux start`, the system automatically ensures the MCP stack is ready:
1.  **Provider Resolution**: Resolves the MCP stack source from project local, vendor, user cache, or package data.
2.  **Materialization**: Creates a symlink or copy of the MCP servers in `docker/mcp-servers`.
3.  **Instance Overlay**: Generates deterministic port allocations and instance-scoped environment/compose overrides in `.dopemux/instances/<instance_id>/`.
4.  **Deterministic Ports**: Each instance gets a dedicated port range (e.g., Instance A starts at 3000, B at 3100) to prevent collisions.

### 3. Phase 0 Discovery Gate (Fail-Closed)

Before any work begins, Dopemux runs a discovery gate that:
1.  **Resolves** endpoints based on priority.
2.  **Probes** endpoints via JSON-RPC POST `tools/list`.
3.  **Validates** that required tool globs (e.g., `conport_*`, `serena_*`) are satisfied.
4.  **Blocks** execution if mandatory tools are missing or unreachable.

**Proof Artifacts**:
Each run generates reports in `proof/latest/`:
- `INSTANCE_RESOLUTION.json`: Provenance of resolved endpoints.
- `DISCOVERY_REPORT.json`: List of available tools per server.
- `PHASE0_REPORT.json`: Final transport reachability and tool count.
- `GATE_RESULT.json`: Final PASS/BLOCK status.

## Enhanced ConPort MCP Implementation

ConPort has been upgraded from a static status shim to a full JSON-RPC tool server.

### 1. Unified Logic
All business logic is now extracted into pure async internal methods, shared between legacy HTTP endpoints and the new MCP interface.

### 2. Supported Discovery Aliases
The `/mcp` endpoint supports multiple discovery method names for compatibility:
- `tools/list` (Canonical)
- `list_tools`, `mcp.listTools`, `tools.list`, `listTools`

### 3. Tool Surface
- **Context**: `conport_get_context`, `conport_update_context`
- **Decisions**: `conport_log_decision`, `conport_get_decisions`
- **Progress**: `conport_log_progress`, `conport_get_progress`, `conport_update_progress`
- **Activity**: `conport_get_recent_activity`, `conport_get_active_work`
- **Instance Management**: `conport_fork_instance`, `conport_promote`, `conport_promote_all`

## Service Integration Architecture

```
Agents → MCP Interface → [Dope-Memory, ConPort, Serena, Dope-Context]
                       ↓
                  EventBus (Redis Streams)
                       ↓
                  Chronicle Store (SQLite)
```

## Verification

To verify that dope-memory is now properly started:

1. Run `dopemux start`
2. Check that dope-memory appears in the service status
3. Verify health check: `curl http://localhost:3020/health`
4. Test MCP interface: `curl http://localhost:3020/mcp`

## Troubleshooting

**Issue**: Dope-memory not starting
- **Check**: `docker-compose ps` in `docker/mcp-servers/`
- **Fix**: Ensure `docker-compose.yml` exists and includes dope-memory service

**Issue**: MCP calls failing
- **Check**: Service health endpoints
- **Fix**: Verify MCP server configuration in `.claude.json`

**Issue**: Memory not persisting
- **Check**: Volume mounting in docker-compose.yml
- **Fix**: Ensure `dope_memory_data` volume is properly configured

## Next Steps

1. **Update Documentation**: Add this integration guide to the main documentation
2. **Test Agents**: Verify existing agents work with the new service setup
3. **Performance Tuning**: Optimize service startup order and dependencies
4. **Monitoring**: Add monitoring for dope-memory service health and usage
