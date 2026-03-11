# TRANSPORT_AND_RUNBOOK.md — Serena v2

Analyzed ref: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

## 1. Transport Summary

| Transport | File | Mechanism | Port | Codebase |
|-----------|------|-----------|------|----------|
| **stdio** (primary) | `mcp_server.py:5362` | `mcp.server.stdio.stdio_server()` | N/A (stdin/stdout) | `services/serena/` |
| **HTTP** (dashboard) | `http_server.py:54` | FastAPI + uvicorn | 8003 | `services/serena/` |
| **SSE** (Docker) | `docker/mcp-servers-source/serena/wrapper.py:34` | mcp-proxy wrapping `serena start-mcp-server` | 3006 | **upstream oraios/serena** |
| **HTTP** (Docker info) | `docker/mcp-servers-source/serena/info_server.py` | FastAPI + uvicorn | 4006 | Docker wrapper |

**CRITICAL**: The SSE Docker transport wraps the **upstream oraios/serena pip package**, NOT the `services/serena/mcp_server.py` code. These are two entirely different server implementations.

## 2. stdio Transport (Primary)

### Entry Point
```python
# mcp_server.py:5326
async def main():
    server_instance = SerenaV2MCPServer()
    await server_instance.initialize()
    server_instance.register_tools()
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream, write_stream,
            server_instance.server.create_initialization_options()
        )
```

### Startup Command
```bash
python services/serena/mcp_server.py
```

### MCP SDK Usage
- Server: `mcp.server.Server("serena-v2")`
- Transport: `mcp.server.stdio.stdio_server`
- Response type: `mcp.types.TextContent(type="text", text=<json_string>)`
- Tool definition: `mcp.types.Tool(name=..., description=..., inputSchema=...)`

### Initialization Sequence
1. `SerenaV2MCPServer.__init__()` — sets up lazy component tracking
2. `initialize()` — detects workspace (git root), starts file watcher
3. `register_tools()` — registers list_tools and call_tool handlers
4. `stdio_server()` — opens stdin/stdout MCP transport
5. `server.run()` — enters event loop

### Lazy Component Loading
Components load on first tool use via `_ensure_component(name)`:
- `database` — PostgreSQL via asyncpg
- `lsp` — Language Server Protocol client (pylsp)
- `claude_context` — Dope-Context integration
- `tree_sitter` — Tree-sitter AST analysis
- `adhd_features` — ADHD code navigator
- `conport` — ConPort database client
- `navigation_cache` — Redis cache
- `file_watcher` — Filesystem watcher (loaded at startup)

## 3. HTTP Transport (Dashboard)

### Entry Point
```python
# http_server.py:572
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
```

### Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Root/landing page |
| `/health` | GET | Health check |
| `/api/metrics` | GET | Aggregated metrics |
| `/api/detections/summary` | GET | Detection summary |
| `/api/patterns/top` | GET | Top patterns |
| `/api/patterns/{pattern_id}` | GET | Pattern detail |

### Notes
- Standalone process, separate from MCP server
- Uses mock data with real aggregator fallback
- ADHD-friendly formatting via `format_adhd_friendly()`

## 4. SSE Transport (Docker)

### Docker Build
```dockerfile
# docker/mcp-servers-source/serena/Dockerfile
FROM python:3.11-slim
RUN pip install "git+https://github.com/oraios/serena.git" mcp-proxy fastapi uvicorn
COPY wrapper.py info_server.py start_with_info.sh /app/
CMD ["bash", "/app/start_with_info.sh"]
```

### Docker Compose (compose.yml)
```yaml
serena:
  build:
    context: ./docker/mcp-servers/serena  # NOTE: different path than Dockerfile location
  ports:
    - "${SERENA_PORT:-3006}:3006"
    - "${SERENA_HTTP_PORT:-4006}:4006"
  environment:
    - MCP_SERVER_PORT=3006
    - HTTP_PORT=4006
    - WORKSPACE_ID=${WORKSPACE_ID:-/workspace}
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:4006/health || exit 1"]
```

### Wrapper Command
```bash
mcp-proxy --transport sse --port 3006 --host 0.0.0.0 --allow-origin '*' -- serena start-mcp-server
```

**WARNING**: `serena start-mcp-server` runs the upstream oraios/serena package, not `services/serena/mcp_server.py`.

## 5. Environment Variables

| Variable | Default | Used By | Purpose |
|----------|---------|---------|---------|
| `MCP_SERVER_PORT` | `3006` | Docker wrapper | SSE transport port |
| `HTTP_PORT` | `4006` | Docker info server | Info/health port |
| `WORKSPACE_ID` | `/workspace` | Docker compose | Workspace identifier |
| `HOST_CODE_PARENT_DIR` | `/tmp` | Docker compose | Volume mount for workspaces |
| `CONPORT_DB_PASSWORD` | `dopemux_age_dev_password` | `conport_client_unified.py` | ConPort PostgreSQL password |
| `WORKSPACE_ROOT` | `Path.cwd()` | `conport_client_unified.py` | Workspace ID for ConPort |

## 6. Health Checks

| Component | Endpoint | Port | Method |
|-----------|----------|------|--------|
| Docker info server | `/health` | 4006 | HTTP GET |
| HTTP dashboard | `/health` | 8003 | HTTP GET |
| MCP stdio server | `get_workspace_status` tool | N/A | MCP call_tool |
| Redis | `ping()` | 6379 | Redis protocol |
| PostgreSQL (intelligence) | Connection pool creation | asyncpg | TCP |
| ConPort | Connection via `ConPortDBClient` | 5455 | PostgreSQL |

## 7. Startup Runbook

### Local Development (stdio)
```bash
cd /Users/hue/code/dopemux-mvp
python services/serena/mcp_server.py
```

### Docker (SSE via compose)
```bash
docker compose up serena
# Health check: curl http://localhost:4006/health
```

### Dashboard (HTTP, separate process)
```bash
cd /Users/hue/code/dopemux-mvp/services/serena
python http_server.py
# Health check: curl http://localhost:8003/health
```

### Dependencies Required
- PostgreSQL with AGE extension (port 5455 for ConPort, asyncpg for intelligence DB)
- Redis (port 6379, db_index=1 for navigation cache)
- Python 3.11+ with: mcp, asyncpg, redis, pydantic, tree-sitter (optional), fastapi (dashboard)
- LSP server (pylsp, optional — fallback to grep if unavailable)
