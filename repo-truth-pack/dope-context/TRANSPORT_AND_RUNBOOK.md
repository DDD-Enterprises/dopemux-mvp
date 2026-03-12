# TRANSPORT_AND_RUNBOOK.md — dope-context

**Analyzed ref:** `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

---

## 1. Transport Summary

| Transport | Supported | Default Port | When Selected | Evidence |
|-----------|-----------|-------------|---------------|----------|
| **stdio** | ✅ | N/A | Default (no PORT env set) | server.py:101 |
| **http** | ✅ | 3010 | `MCP_SERVER_PORT` set | server.py:99, Dockerfile:30 |
| **sse** | ✅ | 3010 | Explicit `MCP_TRANSPORT=sse` | server.py:103 |
| **streamable-http** | ✅ | 3010 | Explicit `MCP_TRANSPORT=streamable-http` | server.py:103 |

---

## 2. Transport Resolution Logic

**Function:** `_resolve_transport_runtime()` (server.py:93-126)

```
Step 1: Check MCP_TRANSPORT or FASTMCP_TRANSPORT
  → If set: normalize to lowercase, validate against {"stdio", "http", "sse", "streamable-http"}
  → If invalid: warn and default to "stdio"

Step 2: If no transport env, check MCP_SERVER_PORT
  → If set: default to "http"

Step 3: If neither set:
  → Default to "stdio"

Host resolution:
  MCP_SERVER_HOST → FASTMCP_HOST → "0.0.0.0"

Port resolution:
  MCP_SERVER_PORT → FASTMCP_PORT → PORT → 3010
```

---

## 3. Transport: stdio

### When Used
- Default for local CLI integration (Claude Code, VS Code)
- Used by `dope-context-wrapper.sh` via `docker exec -i`

### Configuration
No additional configuration required. No port binding.

### Connection Example
```json
{
  "mcpServers": {
    "dope-context": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "env": {
        "VOYAGE_API_KEY": "...",
        "QDRANT_URL": "localhost"
      }
    }
  }
}
```

### Docker Wrapper (stdio via Docker)
**Script:** `scripts/mcp-wrappers/dope-context-wrapper.sh`

```bash
exec docker exec -i \
  -e DOPEMUX_WORKSPACE_ID=... \
  ${CONTAINER} python /app/server.py "$@"
```

**⚠ KNOWN ISSUE:** Wrapper targets `/app/server.py` but actual Docker CMD is `python -m src.mcp.server`. The wrapper path does not match the Docker image layout.

---

## 4. Transport: HTTP

### When Used
- Docker container default (Dockerfile sets `MCP_SERVER_PORT=3010`)
- Compose deployment

### Configuration
```bash
MCP_SERVER_PORT=3010       # Triggers HTTP transport
MCP_SERVER_HOST=0.0.0.0    # Bind address (default)
```

### Startup Command
```bash
# Direct
python -m src.mcp.server

# Docker
docker run -p 3010:3010 \
  -e VOYAGE_API_KEY=... \
  -e QDRANT_URL=http://qdrant:6333 \
  -e MCP_SERVER_PORT=3010 \
  dope-context
```

### Connection URL
`http://localhost:3010/mcp` (computed by `_transport_connection_url`)

### Available HTTP Endpoints
| Path | Method | Purpose | Evidence |
|------|--------|---------|----------|
| `/mcp` | POST | MCP protocol endpoint (FastMCP built-in) | FastMCP framework |
| `/health` | GET | Container health probe | server.py:145-148 |
| `/info` | GET | Service discovery (ADR-208) | server.py:151-195 |
| `/autoindex/bootstrap` | POST | Startup bootstrap indexing | server.py:198-250 |
| `/autoindex/status` | GET | Autoindex progress query | server.py:253-279 |

---

## 5. Transport: SSE

### When Used
- Explicit `MCP_TRANSPORT=sse`
- Legacy MCP client compatibility

### Configuration
```bash
MCP_TRANSPORT=sse
MCP_SERVER_PORT=3010
```

### Connection Example
```json
{
  "mcpServers": {
    "dope-context": {
      "type": "sse",
      "url": "http://localhost:3010/mcp"
    }
  }
}
```

---

## 6. Transport: streamable-http

### When Used
- Explicit `MCP_TRANSPORT=streamable-http`
- New MCP protocol support

### Configuration
```bash
MCP_TRANSPORT=streamable-http
MCP_SERVER_PORT=3010
```

---

## 7. Health Check

### Endpoint
`GET /health` → `{"status": "ok"}`

### Docker Health Check (compose.yml)
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3010/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 45s
```

### Dockerfile Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:3010/health || exit 1
```

---

## 8. Service Discovery (ADR-208)

### Endpoint
`GET /info`

### Response Shape
```json
{
  "name": "dope-context",
  "version": "1.0.0",
  "fastmcp_available": true,
  "canonical_entrypoint": "python -m src.mcp.server",
  "mcp": {
    "protocol": "sse",
    "connection": {
      "type": "sse",
      "url": "http://localhost:3010/mcp"
    },
    "env": {
      "VOYAGE_API_KEY": "${VOYAGEAI_API_KEY:-}",
      "OPENAI_API_KEY": "${OPENAI_API_KEY:-}",
      "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY:-}"
    }
  },
  "runtime": {
    "transport": "http",
    "host": "0.0.0.0",
    "port": 3010,
    "fastmcp_available": true,
    "canonical_entrypoint": "python -m src.mcp.server"
  },
  "health": "/health",
  "description": "Semantic code search and autonomous indexing",
  "metadata": {
    "role": "workflow",
    "priority": "high",
    "adhd_integration": true,
    "autonomous_indexing": true,
    "conport_integration": false,
    "warning": null
  }
}
```

---

## 9. Environment Variables

### Required
| Variable | Purpose | Default | Evidence |
|----------|---------|---------|----------|
| `VOYAGE_API_KEY` or `VOYAGEAI_API_KEY` | Voyage AI API key | None (required) | server.py:465, 776-792 |

### Optional — Transport
| Variable | Purpose | Default | Evidence |
|----------|---------|---------|----------|
| `MCP_TRANSPORT` | Explicit transport | Auto-detect | server.py:95 |
| `FASTMCP_TRANSPORT` | Fallback transport | Auto-detect | server.py:95 |
| `MCP_SERVER_PORT` | Server port | 3010 | server.py:116-119 |
| `FASTMCP_PORT` | Fallback port | 3010 | server.py:116 |
| `PORT` | Fallback port | 3010 | server.py:117 |
| `MCP_SERVER_HOST` | Bind host | 0.0.0.0 | server.py:109 |
| `FASTMCP_HOST` | Fallback host | 0.0.0.0 | server.py:110 |

### Optional — Services
| Variable | Purpose | Default | Evidence |
|----------|---------|---------|----------|
| `OPENAI_API_KEY` | Context generation | None (optional) | server.py:801 |
| `QDRANT_URL` | Qdrant connection | `localhost` | server.py:803 |
| `QDRANT_PORT` | Qdrant port | `6333` | server.py:804 |
| `DOPECON_BRIDGE_URL` | Decision bridge | `http://localhost:3016` | server.py:1860 |
| `WORKSPACE_ID` | Workspace identifier | `"default"` | server.py:847 |

### Optional — Feature Flags
| Variable | Purpose | Default | Evidence |
|----------|---------|---------|----------|
| `FEATURE_ADHD_ENGINE_DOPE_CONTEXT` | ADHD dynamic top_k | Disabled | server.py:327 (Redis flag) |

---

## 10. Startup Runbook

### Local Development (stdio)
```bash
cd services/dope-context
export VOYAGE_API_KEY=your_key
export QDRANT_URL=localhost
python -m src.mcp.server
```

### Docker Compose
```bash
# Set environment
export VOYAGE_API_KEY=your_key
export HOST_CODE_PARENT_DIR=/path/to/code

# Start dependencies + service
docker compose up mcp-qdrant mcp-dope-context

# Verify health
curl http://localhost:3010/health
# → {"status": "ok"}

# Check service info
curl http://localhost:3010/info
```

### Bootstrap Indexing
```bash
# Trigger bootstrap for a workspace
curl -X POST http://localhost:3010/autoindex/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"workspace_path": "/workspaces/my-project", "wait_for_completion": true}'

# Check status
curl http://localhost:3010/autoindex/status
```

### Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| `Voyage API key not set` | `echo $VOYAGE_API_KEY` | Set `VOYAGE_API_KEY` or `VOYAGEAI_API_KEY` |
| Health check fails | `curl localhost:3010/health` | Check container logs: `docker logs mcp-dope-context` |
| Collection empty | MCP tool: `get_index_status` | Run `index_workspace` first |
| BM25 cache load fail | Check `~/.dope-context/snapshots/` | Non-fatal, dense search still works |
| ADHD Engine unavailable | Check Redis and adhd_engine service | Non-fatal, uses default top_k |
| Decision search empty | Check dopecon-bridge at 3016 | Non-fatal, returns empty array |
