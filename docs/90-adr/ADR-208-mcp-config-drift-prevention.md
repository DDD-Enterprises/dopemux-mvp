---
title: 'ADR-208: MCP Configuration Drift Prevention via Service Discovery'
status: accepted
date: 2026-02-03
author: Dopemux Architecture Team
tags:
- mcp
- architecture
- service-discovery
- automation
- docker
category: reference
related:
- ADR-007
- ADR-012
- ADR-207
id: ADR-208-mcp-config-drift-prevention
type: adr
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
prelude: 'ADR-208: MCP Configuration Drift Prevention via Service Discovery (adr)
  for dopemux documentation and developer workflows.'
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# ADR-208: MCP Configuration Drift Prevention via Service Discovery

## Status
**Accepted** (2026-02-03)

## Context

During the migration from local stdio-based MCP servers to containerized HTTP/SSE servers (commit d513a77c), we discovered a critical configuration drift problem:

### The Problem
When infrastructure evolves (local → Docker, stdio → HTTP), client configurations (`.claude.json`) lag behind, creating three failure modes:

1. **Symptom Mismatch**: Servers report "healthy" in Docker, but clients can't connect
1. **Protocol Misalignment**: Config expects stdio/files, servers provide HTTP/SSE
1. **Commit Gap**: Infrastructure changes without corresponding config commits

### Concrete Example
```json
// .claude.json - OUTDATED
{
  "gpt-researcher": {
    "type": "stdio",
    "command": "docker",
    "args": ["exec", "-i", "mcp-gptr-mcp", "python", "/app/server.py"]
  }
}

// docker-compose.yml - ACTUAL STATE
services:
  gptr-mcp:
    ports: ["3009:3009"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3009/health"]
```

**Impact**: Client bypasses HTTP benefits (health checks, network debugging, port isolation) and wraps HTTP server in stdio mode via `docker exec`.

### Audit Results
Out of 12+ MCP servers:
- **40% aligned** (4/10 in .claude.json)
- **50% drifted** (stdio wrappers around HTTP servers)
- **10% missing** (running but not configured)

See `/session-state/*/mcp-drift-audit.md` for full analysis.

## Decision

Implement **automated service discovery** to eliminate manual config sync:

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  MCP Servers (Docker Containers)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Server A │  │ Server B │  │ Server C │          │
│  │  /info   │  │  /info   │  │  /info   │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
└───────┼────────────┼─────────────┼─────────────────┘
        │            │             │
        ▼            ▼             ▼
┌─────────────────────────────────────────────────────┐
│  scripts/generate-claude-config.py                  │
│  - Discover running containers                      │
│  - Query /info endpoints                            │
│  - Generate .claude.json                            │
└───────────────────────┬─────────────────────────────┘
                        ▼
                 .claude.json
            (auto-generated, never manual)
```

### Implementation Components

#### 1. Standard `/info` Endpoint
Every MCP server exposes:
```python
@app.get("/info")
async def info():
    return {
        "name": "gpt-researcher",
        "version": "1.0.0",
        "mcp": {
            "protocol": "sse",  # or "stdio"
            "connection": {
                "type": "sse",
                "url": "http://localhost:3009/sse"
            }
        },
        "health": "/health",
        "description": "Deep research with comprehensive analysis"
    }
```

**Benefits**:
- Single source of truth (server advertises its own config)
- Version tracking built-in
- Protocol evolution tracked automatically

#### 2. Auto-Generation Script
`scripts/generate-claude-config.py`:
```python
#!/usr/bin/env python3
"""
Generate .claude.json from running MCP server containers.

Usage:
    python scripts/generate-claude-config.py > .claude.json
    python scripts/generate-claude-config.py --validate  # Check drift
"""

import docker
import requests
import json

def discover_mcp_servers():
    """Find all running MCP containers and query /info endpoints."""
    client = docker.from_env()
    servers = {}

    for container in client.containers.list():
        if 'mcp-' in container.name or 'conport' in container.name:
            port = extract_port(container)
            if port:
                info = fetch_info(f"http://localhost:{port}/info")
                if info:
                    servers[info['name']] = build_config(info)

    return servers

def build_config(info):
    """Transform /info response into .claude.json format."""
    mcp = info['mcp']

    if mcp['protocol'] == 'sse':
        return {
            "type": "sse",
            "url": mcp['connection']['url'],
            "description": info['description']
        }
    elif mcp['protocol'] == 'stdio':
        return {
            "type": "stdio",
            "command": mcp['connection']['command'],
            "args": mcp['connection']['args'],
            "description": info['description']
        }
```

**Features**:
- Automatic discovery via Docker API
- Health validation before config generation
- Drift detection mode (`--validate`)

#### 3. CI/CD Integration
```bash
# .github/workflows/validate-mcp-config.yml
- name: Validate MCP Configuration
  run: |
    docker-compose up -d
    python scripts/generate-claude-config.py --validate
    # Fails if .claude.json doesn't match running servers
```

## Why HTTP/SSE is Superior for Docker MCP Servers

### Technical Benefits
1. **Health Checks Work**: `curl http://localhost:3009/health`
1. **Network Debugging**: Standard HTTP tools apply (curl, tcpdump, wireshark)
1. **Port Isolation**: Each server isolated, prevents conflicts
1. **No Wrapper Scripts**: Direct connection, simpler architecture

### Operational Benefits
1. **Monitoring**: Prometheus metrics at `/metrics`
1. **Load Balancing**: Standard HTTP load balancers work
1. **Security**: mTLS, API keys, rate limiting all standard
1. **Logging**: Access logs, error logs, structured logging

### Comparison
```
STDIO (via docker exec):
❌ No health checks
❌ No network debugging
❌ Wrapper complexity
❌ No load balancing
✅ Simple for local dev

HTTP/SSE:
✅ curl http://localhost:3009/health
✅ Standard network tools
✅ No wrappers needed
✅ Load balancer ready
✅ Production-grade
```

**Conclusion**: HTTP/SSE is architecturally superior for containerized services. Use stdio only for truly local development.

## Migration Strategy

### Phase 1: Add `/info` Endpoints (Immediate)
Update all MCP servers to expose `/info`:
- gpt-researcher
- exa
- desktop-commander
- pal (missing from .claude.json)
- task-orchestrator
- pal

**Timeline**: 1-2 days

### Phase 2: Implement Auto-Generation (Short-term)
Build `scripts/generate-claude-config.py`:
- Docker discovery
- Health validation
- Drift detection mode

**Timeline**: 1 week

### Phase 3: CI/CD Validation (Short-term)
Add validation to GitHub Actions:
- Run on every MCP server change
- Fail if drift detected
- Auto-generate PR with updated config

**Timeline**: 1 week

### Phase 4: Service Registry (Long-term)
Central service discovery:
- Servers self-register on startup
- Dynamic client configuration
- Health monitoring dashboard

**Timeline**: 1 month

## Consequences

### Positive
1. **Eliminates Manual Sync**: Config generated from running state
1. **Prevents Drift**: CI/CD catches mismatches immediately
1. **Single Source of Truth**: Servers advertise their own config
1. **Version Tracking**: `/info` includes version, tracks evolution
1. **Easier Onboarding**: New developers run one script

### Negative
1. **Initial Migration Cost**: All servers need `/info` endpoint
1. **Tooling Dependency**: Requires Python + Docker SDK
1. **Runtime Dependency**: Must have servers running to generate config

### Neutral
1. **Breaking Change**: Existing manual .claude.json workflows deprecated
1. **New Convention**: Developers must understand service discovery pattern

## Validation

### Success Criteria
1. ✅ All MCP servers expose `/info` endpoint
1. ✅ `generate-claude-config.py` produces valid .claude.json
1. ✅ CI/CD validates on every change
1. ✅ Zero drift between running servers and client config

### Testing
```bash
# Start all servers
docker-compose up -d

# Generate config
python scripts/generate-claude-config.py > .claude.json.generated

# Validate against current
diff .claude.json .claude.json.generated

# Should be identical (or fail CI)
```

## Related Decisions
- **ADR-007**: MCP Server Prioritization
- **ADR-012**: Three-Layer MCP Architecture
- **ADR-207**: Three-Plane Integration Pattern

## References
- MCP Specification: https://modelcontextprotocol.io/docs
- Docker API: https://docker-py.readthedocs.io/
- Session Audit: `/session-state/*/mcp-drift-audit.md`
- Commit d513a77c: Docker migration that introduced drift

## Notes
This ADR captures architectural lessons from real-world infrastructure evolution. The pattern applies beyond MCP servers to any microservices architecture where client config lags behind server deployment.

**Prevention > Detection > Remediation**. Service discovery prevents drift at the source.
