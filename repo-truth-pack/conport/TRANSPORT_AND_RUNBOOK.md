# ConPort — Transport and Runbook

**Analyzed Ref**: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**Source**: `docker/mcp-servers-source/conport/`

---

## 1. Transport Summary

| Transport | Server File | Port | Framework | Protocol |
|---|---|---|---|---|
| HTTP REST | `enhanced_server.py` | 3004 | aiohttp | HTTP/1.1 JSON |
| JSON-RPC over HTTP | `enhanced_server.py` (POST /mcp) | 3004 | aiohttp | JSON-RPC 2.0 |
| SSE (MCP) | `server.py sse` | 3005 | FastMCP/uvicorn | MCP over SSE |
| stdio (MCP) | `server.py` | N/A | FastMCP | MCP over stdio |
| stdio (MCP admin) | `conport_mcp_stdio.py` | N/A | FastMCP | MCP over stdio |
| HTTP (info) | `info_server.py` | 4004 | FastAPI/uvicorn | HTTP/1.1 JSON |

---

## 2. HTTP REST Transport (Primary)

### 2.1 Configuration

| Setting | Env Var | Default | Source |
|---|---|---|---|
| Port | `MCP_SERVER_PORT` | `3004` | `enhanced_server.py` line 90 |
| Host | — | `0.0.0.0` | `enhanced_server.py` line 91 |
| Database URL | `DATABASE_URL` | `postgresql://dopemux_age:...@dopemux-postgres-age:5432/dopemux_knowledge_graph` | line 112-115 |
| Redis URL | `REDIS_URL` | `redis://redis-primary:6379` | line 116 |
| DopeconBridge URL | `DOPECON_BRIDGE_URL` | `http://dope-decision-graph-bridge:3016` | `integration_bridge_client.py` line 43 |
| DB Pool Min | `DB_POOL_MIN` | `5` | line 124 |
| DB Pool Max | `DB_POOL_MAX` | `20` | line 125 |
| Auto Fork | `DOPEMUX_AUTO_FORK_PROGRESS` | `'1'` (enabled) | line 146 |
| Instance ID | `DOPEMUX_INSTANCE_ID` | `None` | `instance_detector.py` line 49 |
| Workspace ID | `DOPEMUX_WORKSPACE_ID` | `cwd` | `instance_detector.py` line 50 |
| Workspace ID (monitoring) | `WORKSPACE_ID` | — | line 105 |
| Instance ID (monitoring) | `INSTANCE_ID` | — | line 106 |
| Service Version | `SERVICE_VERSION` | `"1.0.0"` | line 107 |

### 2.2 Startup Sequence

1. `EnhancedConPortServer.__init__()` — configure app, routes, monitoring
2. `start_server()` → `init_connections()`:
   a. Create asyncpg connection pool
   b. `_ensure_schema()` — check for `workspace_contexts` table, apply `schema.sql` via psql if missing
   c. Add `instance_id` columns if missing (lines 478-483)
   d. Connect to Redis, verify with PING
   e. Initialize DopeconBridge client (optional, degrades gracefully)
   f. Initialize UnifiedQueryAPI (optional)
   g. Start auto-save loop (30s interval asyncio task)
3. Create aiohttp runner and TCPSite, bind to host:port
4. Wait for shutdown signal (SIGTERM/SIGINT)

**Source**: `enhanced_server.py` lines 2093-2116, 155-217

### 2.3 Health Check

```
GET /health
```

**Response (healthy)**:
```json
{
  "status": "healthy",
  "service": "conport-enhanced",
  "port": 3004,
  "database": "healthy",
  "redis": "healthy",
  "timestamp": 1234567890.123
}
```

**Response (unhealthy, 503)**:
```json
{
  "status": "unhealthy",
  "error": {"type": "SERVICE_UNAVAILABLE", ...},
  "timestamp": 1234567890.123
}
```

**Docker healthcheck** (`Dockerfile` line 35-36):
```
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3
    CMD curl -f http://localhost:3004/health || exit 1
```

### 2.4 Shutdown

- Signal handlers for SIGTERM, SIGINT
- Cancels auto-save task
- Closes DopeconBridge session
- Closes Redis connection
- Closes asyncpg pool
- Cleanup aiohttp runner

**Source**: `enhanced_server.py` lines 2118-2145

---

## 3. JSON-RPC Transport

### 3.1 Endpoint

```
POST /mcp
Content-Type: application/json
```

### 3.2 Request Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "conport_get_context",
    "arguments": {"workspace_id": "dopemux-mvp"}
  }
}
```

Or direct method invocation:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "conport_get_context",
  "params": {"workspace_id": "dopemux-mvp"}
}
```

### 3.3 Discovery

**Methods accepted**: `tools/list`, `list_tools`, `mcp.listTools`, `tools.list`, `listTools`

Returns 9 tool schemas (3 instance management tools are undiscoverable but callable).

### 3.4 Invocation

**Methods accepted**: `tools/call`, `tool/call`, or any method starting with `conport_`

### 3.5 Response Format

**Success**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { ... }
}
```

**Error**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Tool not found: unknown_tool"
  }
}
```

**Error codes used**:
| Code | Meaning |
|---|---|
| -32600 | Invalid Request (missing method) |
| -32601 | Method not found |
| -32602 | Invalid params (missing tool name) |
| -32603 | Internal error |
| -32000 | Application error (handler returned error dict) |

**Note**: JSON-RPC errors return HTTP 200 (per JSON-RPC convention). Source: `enhanced_server.py` line 1728.

---

## 4. SSE Transport (MCP Protocol)

### 4.1 Configuration

| Setting | Env Var | Default | Source |
|---|---|---|---|
| Port | `MCP_SERVER_PORT` | `3005` (overridden by `start_with_info.sh`) | `server.py` line 10 |
| ConPort Backend | `CONPORT_URL` | `http://localhost:3004` | `server.py` line 9 |

### 4.2 Startup

```bash
MCP_SERVER_PORT=3005 python server.py sse
```

Creates FastMCP SSE app and serves via uvicorn at `0.0.0.0:3005`.

**Source**: `server.py` lines 173-175

### 4.3 Client Configuration

From `.claude.json`:
```json
{
  "dopemux-conport": {
    "type": "sse",
    "url": "http://localhost:3005/mcp"
  }
}
```

### 4.4 Tool Surface

13 tools registered via `@mcp.tool()` decorator. All tools delegate to `enhanced_server.py` HTTP API at `CONPORT_URL`.

---

## 5. stdio Transport (MCP Protocol)

### 5.1 server.py stdio mode

```bash
python server.py
# or
python server.py stdio
```

Uses `mcp.run(transport="stdio")`. Same 13 tools as SSE mode.

**Source**: `server.py` lines 176-177

### 5.2 conport_mcp_stdio.py (admin client)

```bash
python conport_mcp_stdio.py
```

Uses `mcp.run_stdio_async()`. FastMCP name: `"conport-admin"`. Same 13 tools with `log_decision` payload difference.

**Source**: `conport_mcp_stdio.py` lines 167-174

---

## 6. Info Sidecar Transport

### 6.1 Configuration

| Setting | Value | Source |
|---|---|---|
| Port | 4004 (PORT + 1000) | `info_server.py` line 19 |
| Framework | FastAPI | `info_server.py` line 21 |

### 6.2 Endpoints

**GET /health**:
```json
{"status": "healthy", "service": "conport", "port": 3004}
```

**GET /info** (ADR-208 auto-config):
```json
{
  "name": "conport",
  "version": "1.0.0",
  "mcp": {
    "protocol": "sse",
    "connection": {"type": "sse", "url": "http://localhost:3004/sse"},
    "env": {"WORKSPACE_ID": "${WORKSPACE_ID:-}", ...}
  },
  "health": "/health",
  "description": "Knowledge graph and context management",
  "metadata": {
    "role": "workflow",
    "priority": "high",
    "mcp_proxy_wrapped": true,
    "info_port": 4004,
    "mcp_port": 3004
  }
}
```

---

## 7. Runbook

### 7.1 Docker Start

```bash
# Full stack
docker compose up conport -d

# Smoke stack
docker compose -f docker-compose.smoke.yml up conport -d
```

### 7.2 Local Development

```bash
cd docker/mcp-servers-source/conport

# Start PostgreSQL and Redis first
# Then:
DATABASE_URL=postgresql://... REDIS_URL=redis://... python enhanced_server.py

# In another terminal (for MCP SSE):
CONPORT_URL=http://localhost:3004 MCP_SERVER_PORT=3005 python server.py sse

# For stdio MCP:
CONPORT_URL=http://localhost:3004 python server.py
```

### 7.3 Health Verification

```bash
# HTTP server
curl http://localhost:3004/health

# MCP SSE (via info sidecar)
curl http://localhost:4004/health

# Service info
curl http://localhost:4004/info
```

### 7.4 Schema Management

Schema is auto-applied on startup if `workspace_contexts` table is missing (`_ensure_schema`, `enhanced_server.py` lines 408-483).

Manual migration:
```bash
psql -h localhost -p 5432 -U dopemux_age -d dopemux_knowledge_graph -f schema.sql
psql -h localhost -p 5432 -U dopemux_age -d dopemux_knowledge_graph -f migrations/001_enhanced_decision_model.sql
# etc.
```

### 7.5 Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `health` returns 503 | PostgreSQL or Redis down | Check database/Redis connectivity |
| MCP tools return errors | `enhanced_server.py` not running on :3004 | Verify CONPORT_URL points to running server |
| Empty progress on get | Auto-fork may not have triggered | Check `DOPEMUX_AUTO_FORK_PROGRESS=1` |
| Schema apply fails | psql not available in container | Verify `postgresql-client` installed in Dockerfile |

### 7.6 Monitoring

When `MONITORING_AVAILABLE=True`:
- Prometheus metrics at `GET /metrics`
- Request duration, error counts, in-progress gauge
- Middleware-based instrumentation

### 7.7 Environment Variable Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | (Docker-internal) | PostgreSQL connection string |
| `REDIS_URL` | ✅ | `redis://redis-primary:6379` | Redis connection string |
| `MCP_SERVER_PORT` | ❌ | `3004` / `3005` | HTTP/MCP port |
| `CONPORT_URL` | ❌ | `http://localhost:3004` | Backend URL for MCP proxy |
| `DOPECON_BRIDGE_URL` | ❌ | `http://dope-decision-graph-bridge:3016` | Event bridge URL |
| `DB_POOL_MIN` | ❌ | `5` | Minimum DB connections |
| `DB_POOL_MAX` | ❌ | `20` | Maximum DB connections |
| `DOPEMUX_INSTANCE_ID` | ❌ | `None` | Worktree instance ID |
| `DOPEMUX_WORKSPACE_ID` | ❌ | `cwd` | Workspace root path |
| `DOPEMUX_AUTO_FORK_PROGRESS` | ❌ | `'1'` | Auto-fork on empty get_progress |
| `WORKSPACE_ID` | ❌ | — | Monitoring workspace label |
| `INSTANCE_ID` | ❌ | — | Monitoring instance label |
| `SERVICE_VERSION` | ❌ | `"1.0.0"` | Monitoring version label |
