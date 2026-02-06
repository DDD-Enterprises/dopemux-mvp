# Leantime Bridge MCP Server

**Category**: MCP Server  
**Status**: Production  
**Port**: 3015  
**Purpose**: Project management integration

## Overview

Leantime Bridge provides MCP integration with Leantime project management system, enabling task creation, status tracking, and project coordination from AI assistants.

## Quick Start

```bash
# Start via Docker Compose
cd docker/mcp-servers
docker compose up -d --build leantime-bridge

# Verify connectivity
curl http://localhost:3015/health
```

## Configuration

Environment variables:
- `LEANTIME_API_URL` - Leantime instance URL (default: `http://leantime:80`)
- `LEANTIME_API_TOKEN` - API token for Leantime (recommended)
- `MCP_SERVER_PORT` - MCP server port (default: `3015`)
- `LEAN_TIME_RATE_LIMIT_SECONDS` - API call spacing in seconds (default: `1.0`)

## MCP Tools

- `create_task` - Create new task in Leantime
- `update_task` - Update task status/details
- `list_tasks` - Query tasks by project/status
- `create_project` - Create new project

## Integration with Dopemux

Part of the PM Plane architecture (ADR-207), enabling:
- Task creation from AI conversations
- Automatic status updates
- Project coordination
- ADHD-optimized task breakdown

## Documentation

See [docs/90-adr/](../../../docs/90-adr/) for architecture details.

## Development

```bash
# Test task creation
curl http://localhost:3015/info | jq
```

## Service Discovery

### /info Endpoint

The leantime-bridge now provides a `/info` endpoint for service discovery and auto-configuration:

```bash
curl http://localhost:3015/info | jq
```

**Features**:
- Real-time Leantime health status
- MCP connection configuration (SSE endpoints)
- Service metadata and capabilities
- Auto-configuration support for MCP clients

**Documentation**: See [INFO_ENDPOINT.md](./INFO_ENDPOINT.md)

**Testing**:
```bash
python test_info_endpoint.py
```

This implements ADR-208 service discovery pattern, allowing Dopemux services to auto-detect Leantime Bridge configuration without hardcoded URLs.
