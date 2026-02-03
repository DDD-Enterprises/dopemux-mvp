# Leantime Bridge MCP Server

**Category**: MCP Server  
**Status**: Production  
**Port**: 3013  
**Purpose**: Project management integration

## Overview

Leantime Bridge provides MCP integration with Leantime project management system, enabling task creation, status tracking, and project coordination from AI assistants.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d leantime-bridge

# Verify connectivity
curl http://localhost:3013/health
```

## Configuration

Environment variables:
- `LEANTIME_URL` - Leantime instance URL (required)
- `LEANTIME_API_KEY` - API key for Leantime (required)
- `PORT` - MCP server port (default: 3013)

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
curl -X POST http://localhost:3013/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "project_id": 1}'
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

