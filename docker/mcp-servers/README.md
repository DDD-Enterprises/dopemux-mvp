# Dopemux MCP Servers - Docker Compose Stack

Complete Docker orchestration for Dopemux MCP (Model Context Protocol) servers.

## Quick Start

### Standalone Mode (Default - No Leantime)

```bash
# Start all MCP services WITHOUT Leantime integration
docker compose -f docker/mcp-servers/docker-compose.yml up -d

# Check status
docker compose -f docker/mcp-servers/docker-compose.yml ps

# Stop services
docker compose -f docker/mcp-servers/docker-compose.yml down
```

**Services included**: ConPort, Serena, Dope-Context, GPT-Researcher, LiteLLM, Task Orchestrator, Plane Coordinator, Desktop Commander, Activity Capture, Redis, Qdrant

### Linked Mode (With Leantime Integration)

**Prerequisites**:
1. Leantime stack must be running
2. `leantime-net` network must exist

**Preflight check**:
```bash
# Verify Leantime network exists
docker network ls | grep leantime-net

# If missing, start Leantime first
docker compose -f docker/leantime/docker-compose.yml up -d
```

**Start linked mode**:
```bash
# Start MCP stack WITH Leantime integration
docker compose -f docker/mcp-servers/docker-compose.yml \
               -f docker/mcp-servers/docker-compose.leantime.yml up -d

# Check status
docker compose -f docker/mcp-servers/docker-compose.yml \
               -f docker/mcp-servers/docker-compose.leantime.yml ps
```

**Additional service**: Leantime Bridge (port 3015)

## Architecture

### Two-File Design

1. **`docker-compose.yml`** (Standalone)
   - Core MCP services
   - No external dependencies on Leantime
   - Can start on clean machines

2. **`docker-compose.leantime.yml`** (Overlay)
   - Adds Leantime Bridge service
   - Declares `leantime-net` as external network
   - Opt-in via multi-file compose

### Why This Design?

**Problem**: Previously, `leantime-net` was declared as a top-level external network in the main compose file. Docker validates ALL external networks before starting ANY services, so one missing network blocked the entire 12-service stack.

**Solution**: Split into standalone (default) and linked (opt-in) layers. This avoids Docker's "validate all externals up front" trap permanently.

## Service Reference

| Service | Port | Description | Transport |
|---------|------|-------------|-----------|
| **conport** | 3004 | Knowledge graph & context | SSE |
| **serena** | 3006, 4006 | ADHD engine & code intelligence | HTTP |
| **dope-context** | 3010 | Semantic code search | HTTP |
| **litellm** | 4000 | LLM proxy & routing | HTTP |
| **task-orchestrator** | 3014 | Task management | HTTP |
| **plane-coordinator** | 8090 | Two-plane coordination | HTTP |
| **desktop-commander** | 3012 | Desktop automation | HTTP |
| **activity-capture** | 8096 | ADHD activity tracking | HTTP |
| **gpt-researcher** | 8000-8001 | Deep research | HTTP/WebSocket |
| **mcp-client** | - | MCP client for stdio servers | - |
| **redis-primary** | - | Shared cache | Redis |
| **qdrant** | 6333-6334 | Vector database | HTTP |
| **leantime-bridge** | 3015 | Leantime integration (linked only) | HTTP/SSE |

## Troubleshooting

### "network leantime-net declared as external, but could not be found"

**Cause**: Attempting linked mode without Leantime running.

**Solution**: Either:
1. Start Leantime first: `docker compose -f docker/leantime/docker-compose.yml up -d`
2. Use standalone mode: `docker compose -f docker/mcp-servers/docker-compose.yml up -d`

### "port is already allocated"

**Cause**: Another container is using the same port.

**Solution**:
```bash
# Find the conflicting container
docker ps | grep <port_number>

# Stop it
docker stop <container_name>
```

### Service keeps restarting

**Causes**:
1. Missing environment variables (check `.env` files)
2. Missing bind-mounted files (e.g., `litellm.config.yaml`)
3. Startup race conditions (some services need others to be ready)

**Solution**:
```bash
# Check logs
docker compose -f docker/mcp-servers/docker-compose.yml logs <service_name>

# For bind mount issues, verify file exists
ls -la <path_in_bind_mount>
```

## Environment Variables

Most services use environment variables defined in:
- Root `.env` file (project-wide)
- Service-specific `.env` files (e.g., `./leantime-bridge/.env`)

**Common variables**:
- `DOPEMUX_STACK_PREFIX`: Container name prefix (default: `dopemux`)
- `DOPEMUX_WORKSPACE_ID`: Workspace path for context isolation
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.: API keys for LLM services
- `ENABLE_LEANTIME`: Set to `1` to enable Leantime integration

## Development

### Rebuilding Services

```bash
# Rebuild specific service
docker compose -f docker/mcp-servers/docker-compose.yml build <service_name>

# Rebuild all
docker compose -f docker/mcp-servers/docker-compose.yml build

# Rebuild and restart
docker compose -f docker/mcp-servers/docker-compose.yml up -d --build
```

### Viewing Logs

```bash
# All services
docker compose -f docker/mcp-servers/docker-compose.yml logs -f

# Specific service
docker compose -f docker/mcp-servers/docker-compose.yml logs -f <service_name>

# Last 100 lines
docker compose -f docker/mcp-servers/docker-compose.yml logs --tail=100
```

## Networks

- **dopemux-network**: Main MCP network (external, must exist)
- **mcp-network**: Alias for dopemux-network
- **leantime-net**: Leantime integration network (overlay only, external)

## Volumes

Persistent data volumes (local driver):
- `mcp_*_data`: Service data
- `mcp_*_logs`: Service logs
- `mcp_*_cache`: Cache storage
- `pg_age_data`: PostgreSQL data (external)

## Dopemux CLI Integration

The `dopemux mcp start-all` command automatically uses the standalone compose file.

**Enable Leantime integration**:
```bash
ENABLE_LEANTIME=1 dopemux mcp start-all
```

## Related Documentation

- [ADR-214: MCP Leantime Decoupling](../../docs/90-adr/ADR-214-mcp-leantime-decoupling.md)
- [ADR-012: MCP Integration](../../docs/90-adr/DOPEMUX-ADR-012-mcp-integration.md)
- [Deployment Guide](../../docs/02-how-to/deployment-guide.md)
