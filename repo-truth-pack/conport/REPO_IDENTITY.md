# ConPort — Repo Identity

| Field | Value |
|---|---|
| **Component Name** | ConPort (Knowledge Graph & Context Management) |
| **Canonical Path** | `docker/mcp-servers-source/conport/` |
| **Repository Root** | `/Users/hue/code/dopemux-mvp` |
| **Analyzed Ref** | `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2` |
| **Analyzed Branch** | `codex/main-drain-20260306` |
| **Language** | Python 3.11 |
| **Framework** | aiohttp (HTTP), FastMCP (MCP protocol), FastAPI (info sidecar) |
| **Version** | `1.0.0` (hardcoded in `info_server.py` line 34) |
| **License** | Governed by parent repository license |
| **Package Manager** | pip (inline in Dockerfile, no requirements.txt) |
| **Test Framework** | pytest (tests in `tests/` subdirectory) |
| **Container Runtime** | Docker (`python:3.11-slim`) |

## Registry Identity

| Registry Key | Port | Health | Smoke | Description |
|---|---|---|---|---|
| `conport-http` | 3004 | `/health` | ✅ enabled | ConPort HTTP API |
| `conport-mcp` | 3005 | `/health` | ❌ disabled | ConPort MCP (SSE) |

**Source**: `services/registry.yaml` lines 87–115

## Compose Identity

| Compose File | Service Name | Container Name | Build Context |
|---|---|---|---|
| `compose.yml` | `conport` | `mcp-conport` | `./docker/mcp-servers/conport` |
| `docker-compose.smoke.yml` | `conport` | `smoke-conport` | `./docker/mcp-servers/conport` |

**Note**: Build context `docker/mcp-servers/conport` does not exist at analyzed ref. Source is at `docker/mcp-servers-source/conport/`. Likely a build-time copy or symlink.

## MCP Client Identity

| Config File | Key | Transport | URL |
|---|---|---|---|
| `.claude.json` | `dopemux-conport` | SSE | `http://localhost:3005/mcp` |

## Dependencies (Runtime)

| Dependency | Purpose | Evidence |
|---|---|---|
| `aiohttp` | HTTP server framework | `enhanced_server.py` line 68 |
| `asyncpg` | PostgreSQL async driver | `enhanced_server.py` line 70 |
| `redis` (aioredis) | Redis async client | `enhanced_server.py` line 71 |
| `mcp` (FastMCP) | MCP protocol SDK | `server.py` line 7 |
| `prometheus-client` | Metrics exposition | `Dockerfile` line 14 |
| `fastapi` | Info server framework | `info_server.py` line 10 |
| `uvicorn` | ASGI server | `server.py` line 168, `info_server.py` line 12 |

**Source**: `Dockerfile` line 14: `pip install uv aiohttp asyncpg redis mcp prometheus-client fastapi uvicorn`

## External Service Dependencies

| Service | Default URL | Env Var | Required |
|---|---|---|---|
| PostgreSQL | `postgresql://dopemux_age:...@dopemux-postgres-age:5432/dopemux_knowledge_graph` | `DATABASE_URL` | ✅ Required |
| Redis | `redis://redis-primary:6379` | `REDIS_URL` | ✅ Required |
| DopeconBridge | `http://dope-decision-graph-bridge:3016` | `DOPECON_BRIDGE_URL` | ❌ Optional (degrades gracefully) |

## File Manifest (Active Files Only)

| File | Lines | Role |
|---|---|---|
| `enhanced_server.py` | 2149 | Primary HTTP+JSON-RPC server |
| `server.py` | 178 | FastMCP SSE/stdio proxy |
| `conport_mcp_stdio.py` | 175 | FastMCP stdio-only admin client |
| `info_server.py` | 62 | Service discovery sidecar |
| `start_with_info.sh` | 19 | Multi-process entrypoint |
| `unified_queries.py` | 361 | Cross-workspace query layer |
| `instance_detector.py` | 197 | Worktree instance detection |
| `integration_bridge_client.py` | 163 | DopeconBridge event publisher |
| `shared_monitoring.py` | 359 | Prometheus monitoring base |
| `schema.sql` | 291 | Base PostgreSQL schema |
| `Dockerfile` | 40 | Container build spec |
| `migrations/*.sql` | 5 files | Schema migrations (001,002,003,004,007) |
