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
