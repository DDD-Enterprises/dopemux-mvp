---
id: mcp-service-discovery-guide
title: Mcp Service Discovery Guide
type: how-to
date: 2026-02-03
author: Dopemux Architecture Team
owner: '@hu3mann'
last_review: '2026-02-03'
next_review: '2026-05-03'
tags: [mcp, service-discovery, implementation, automation]
category: how-to
related: [ADR-208]
prelude: "Step-by-step guide for adding /info endpoints to MCP servers and using auto-generation to eliminate config drift. Includes mcp-proxy wrapper solution."
---

# MCP Service Discovery Implementation Guide

**Related**: ADR-208 - MCP Configuration Drift Prevention via Service Discovery

## Quick Start

### For Server Developers

Add `/info` endpoint to your MCP server:

```python
# Example: FastMCP-based server (exa, desktop-commander, etc.)
@mcp.custom_route("/info", methods=["GET"])
async def service_info(request):
    """Service discovery endpoint - auto-config support (ADR-208)"""
    from starlette.responses import JSONResponse
    port = int(os.getenv("MCP_SERVER_PORT", 3008))

    return JSONResponse({
        "name": "my-server",
        "version": "1.0.0",
        "mcp": {
            "protocol": "sse",  # or "stdio"
            "connection": {
                "type": "sse",
                "url": f"http://localhost:{port}/sse"
            },
            "env": {
                "API_KEY": "${API_KEY:-}"
            }
        },
        "health": "/health",
        "description": "Server description",
        "metadata": {
            "role": "research",  # critical_path, workflow, research, quality, utility
            "priority": "medium",
            "dependencies": ["postgres", "redis"]
        }
    })
```

### For FastAPI Servers

Use the helper module:

```python
from scripts.mcp_service_info import add_info_endpoint

app = FastAPI()

add_info_endpoint(
    app,
    name="gpt-researcher",
    version="1.0.0",
    protocol="sse",
    connection_url="http://localhost:3009/sse",
    description="Deep research with comprehensive analysis",
    env_vars={"OPENAI_API_KEY": "${OPENAI_API_KEY:-}"},
    metadata={"role": "research", "priority": "medium"}
)
```

### Generate .claude.json

```bash
# Start all MCP servers
docker-compose -f compose.yml up -d

# Generate config
python scripts/generate-claude-config.py > .claude.json

# Validate existing config
python scripts/generate-claude-config.py --validate

# Show diff
python scripts/generate-claude-config.py --diff
```

## Migration Checklist

### Phase 1: Add /info Endpoints ✅ (3/12 complete)

- [x] exa (completed)
- [x] conport (completed - mcp-proxy wrapper with parallel info server)
- [x] serena-v2 (completed - mcp-proxy wrapper with parallel info server)
- [ ] gpt-researcher
- [ ] desktop-commander
- [ ] pal
- [ ] task-orchestrator
- [ ] pal
- [ ] leantime-bridge
- [ ] dope-context
- [ ] zen
- [ ] morphllm-fast-apply

### Phase 2: Test Auto-Generation

```bash
# After 3-4 servers have /info, test generation
python scripts/generate-claude-config.py > .claude.json.test
diff .claude.json .claude.json.test
```

### Phase 3: Update Documentation

- [ ] Update SERVER_REGISTRY.md with /info endpoint status
- [ ] Add migration guide to docker/mcp-servers/README.md
- [ ] Update .claude/claude.md with service discovery pattern

### Phase 4: CI/CD Integration

```yaml
# .github/workflows/validate-mcp-config.yml
name: Validate MCP Configuration

on:
  pull_request:
    paths:
- 'docker/mcp-servers/**'
- '.claude.json'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
- uses: actions/checkout@v3

- name: Start MCP Services
        run: |
          cd docker/mcp-servers
          docker-compose up -d
          sleep 10  # Wait for services to be ready

- name: Validate Configuration
        run: |
          python scripts/generate-claude-config.py --validate

- name: Generate PR Comment
        if: failure()
        run: |
          python scripts/generate-claude-config.py --diff > drift-report.txt
          # Post as PR comment
```

## /info Endpoint Specification

### Required Fields

```json
{
  "name": "string",        // Canonical server name
  "version": "string",     // Semantic version (1.0.0)
  "mcp": {
    "protocol": "sse|stdio",
    "connection": {
      // SSE:
      "type": "sse",
      "url": "http://localhost:3009/sse"

      // OR stdio:
      "type": "stdio",
      "command": "python3",
      "args": ["/app/server.py"]
    }
  },
  "health": "/health",
  "description": "string"
}
```

### Optional Fields

```json
{
  "mcp": {
    "env": {
      "API_KEY": "${API_KEY:-}",
      "WORKSPACE_ID": "${WORKSPACE_ID:-}"
    }
  },
  "metadata": {
    "role": "critical_path|workflow|research|quality|utility",
    "priority": "highest|high|medium|low",
    "dependencies": ["postgres", "redis"],
    "stdio_fallback": {
      "command": "docker",
      "args": ["exec", "-i", "container", "python", "/app/server.py"]
    }
  }
}
```

## Server Types

### FastMCP Servers

Already support custom routes - add directly:

```python
@mcp.custom_route("/info", methods=["GET"])
async def service_info(request):
    from starlette.responses import JSONResponse
    return JSONResponse({...})
```

**Examples**: exa, desktop-commander, gpt-researcher

### FastAPI Servers

Use helper module or add route:

```python
from scripts.mcp_service_info import add_info_endpoint

add_info_endpoint(app, name="...", ...)
```

**Examples**: dope-context, leantime-bridge

### MCP-Proxy Wrapped Servers ✅ SOLVED

For servers that use mcp-proxy (stdio → SSE conversion), we run a **parallel HTTP server** for service discovery:

**Architecture**:
```
┌─────────────────────────────────────┐
│  Container (e.g., conport, serena)  │
│                                     │
│  Port 3004 → MCP Server (mcp-proxy) │
│  Port 4004 → Info Server (FastAPI)  │
└─────────────────────────────────────┘
```

**Implementation**:

1. **Info Server** (`info_server.py`):
   ```python
   # Parallel FastAPI server on PORT+1000
   INFO_PORT = PORT + 1000  # e.g., 3004 → 4004

   @app.get("/info")
   async def service_info():
       return {
           "name": "conport",
           "mcp": {
               "protocol": "sse",
               "connection": {
                   "type": "sse",
                   "url": f"http://localhost:{PORT}/sse"
               }
           },
           "metadata": {
               "mcp_proxy_wrapped": True,
               "info_port": INFO_PORT,
               "mcp_port": PORT
           }
       }
   ```

1. **Start Script** (`start_with_info.sh`):
   ```bash
   #!/bin/bash
   # Start both servers in parallel
   python info_server.py &
   python mcp_server.py &
   wait
   ```

1. **Dockerfile**:
   ```dockerfile
   # Install FastAPI + uvicorn
   RUN pip install fastapi uvicorn

   # Copy both servers
   COPY info_server.py .
   COPY start_with_info.sh .

   # Expose both ports
   EXPOSE 3004 4004

   CMD ["bash", "start_with_info.sh"]
   ```

1. **Docker Compose**:
   ```yaml
   ports:
- "3004:3004"  # MCP server
- "4004:4004"  # Info server
   ```

**Benefits**:
- ✅ MCP server runs unchanged (mcp-proxy stdio → SSE)
- ✅ Info server provides /info endpoint on separate port
- ✅ No mcp-proxy modification needed
- ✅ Claude Code uses MCP port (3004)
- ✅ Service discovery uses info port (4004)

**Examples**: conport (ports 3004/4004), serena-v2 (ports 3006/4006)

## Testing

### Manual Test

```bash
# Start server
docker-compose up -d exa

# Query /info
curl http://localhost:3008/info | jq

# Expected output:
{
  "name": "exa",
  "version": "1.0.0",
  "mcp": {
    "protocol": "sse",
    "connection": {
      "type": "sse",
      "url": "http://localhost:3008/sse"
    }
  },
  ...
}
```

### Automated Test

```bash
# Run discovery script
python scripts/generate-claude-config.py --validate

# Should show:
✅ exa: sse configured
```

## Troubleshooting

### Server not discovered

**Symptom**: Server running but not in generated config

**Fixes**:
1. Check container name matches pattern: `mcp-*`, `conport`, `serena`, `leantime-bridge`, `dope-context`
1. Verify port exposed in docker-compose.yml
1. Check health endpoint: `curl http://localhost:{port}/health`

### /info endpoint not responding

**Symptom**: `⚠️  server-name: No /info endpoint (timeout)`

**Fixes**:
1. Server might not have /info yet (expected during migration)
1. Check logs: `docker logs dopemux-mcp-{server}`
1. Verify server running: `docker ps | grep {server}`
1. Test manually: `curl http://localhost:{port}/info`

### Validation fails

**Symptom**: `❌ Configuration drift detected!`

**This is expected during migration** - run:

```bash
python scripts/generate-claude-config.py --diff
```

Review drift and decide:
- Update .claude.json from generated config
- OR fix server /info endpoints to match current config

## Example Implementations

### ✅ Exa (Completed)

See: `docker/mcp-servers/exa/exa_server.py` lines 66-108

### 🚧 GPT Researcher (TODO)

```python
# docker/mcp-servers/gpt-researcher/server.py (ADD THIS)

@mcp.custom_route("/info", methods=["GET"])
async def service_info(request):
    from starlette.responses import JSONResponse
    return JSONResponse({
        "name": "gpt-researcher",
        "version": "1.0.0",
        "mcp": {
            "protocol": "sse",
            "connection": {
                "type": "sse",
                "url": "http://localhost:3009/sse"
            },
            "env": {
                "OPENAI_API_KEY": "${OPENAI_API_KEY:-}",
                "TAVILY_API_KEY": "${TAVILY_API_KEY:-}"
            }
        },
        "health": "/health",
        "description": "Deep research with comprehensive analysis"
    })
```

### 🚧 Desktop Commander (TODO)

Similar pattern - FastMCP server on port 3012

## Benefits

### Before (Manual Config)
```
Infrastructure changes → Forget to update .claude.json → Drift → Connection failures
```

### After (Service Discovery)
```
Infrastructure changes → /info endpoint auto-updated → Generate script → No drift
```

### Metrics
- **Setup time**: 30 min manual → 1 min auto-generate
- **Drift detection**: Manual inspection → Automated CI check
- **Onboarding**: "Edit .claude.json carefully" → "Run one script"

## Next Steps

1. **Immediate**: Add /info to 3-4 more servers (gpt-researcher, desktop-commander, pal)
1. **Short-term**: Generate and validate config, commit to repo
1. **Long-term**: Add CI validation, service registry dashboard

## References

- **ADR-208**: MCP Configuration Drift Prevention
- **Script**: `scripts/generate-claude-config.py`
- **Helper**: `scripts/mcp_service_info.py`
- **Audit**: Session state drift audit (mcp-drift-audit.md)
