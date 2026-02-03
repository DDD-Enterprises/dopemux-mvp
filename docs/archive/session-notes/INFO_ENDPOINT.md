---
id: INFO_ENDPOINT
title: Info_Endpoint
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Leantime Bridge /info Endpoint

## Overview

The `/info` endpoint provides service discovery and auto-configuration information for the Leantime Bridge MCP server. This implements the recommendation from ADR-208 for standardized service metadata.

## Endpoint

```
GET http://localhost:3015/info
```

## Response Format

```json
{
  "name": "leantime-bridge",
  "version": "1.0.0",
  "leantime": {
    "url": "http://leantime:80",
    "status": "healthy|unhealthy|unknown",
    "version": null,
    "rate_limit_seconds": 1.0
  },
  "mcp": {
    "protocol": "sse",
    "endpoints": {
      "sse": "http://localhost:3015/sse",
      "messages": "http://localhost:3015/messages/",
      "health": "http://localhost:3015/health",
      "info": "http://localhost:3015/info"
    },
    "connection": {
      "type": "sse",
      "url": "http://localhost:3015/sse"
    },
    "env": {
      "LEANTIME_API_TOKEN": "${LEANTIME_API_TOKEN:-}"
    }
  },
  "health": "/health",
  "description": "Leantime project management integration bridge (HTTP/SSE transport)",
  "metadata": {
    "role": "workflow",
    "priority": "high",
    "integration": "leantime",
    "transport": "http-sse",
    "plane": "pm_plane",
    "tools_count": 8
  }
}
```

## Fields

### Core Fields
- **name**: Service identifier (`leantime-bridge`)
- **version**: Service version (semver)
- **description**: Human-readable service description

### Leantime Section
- **url**: Leantime API base URL
- **status**: Real-time health status (`healthy`, `unhealthy: <error>`, `unknown`)
- **version**: Leantime version (if detectable)
- **rate_limit_seconds**: Rate limiting configuration

### MCP Section
- **protocol**: MCP protocol version (`sse`)
- **endpoints**: All available HTTP endpoints
  - **sse**: Server-Sent Events endpoint for MCP connection
  - **messages**: POST endpoint for MCP messages
  - **health**: Health check endpoint
  - **info**: This endpoint
- **connection**: MCP client connection configuration
  - **type**: Transport type (`sse`)
  - **url**: Primary connection URL
- **env**: Required environment variables (with defaults)

### Metadata Section
- **role**: Service role in Dopemux architecture (`workflow`)
- **priority**: Service priority (`high`)
- **integration**: External system integrated (`leantime`)
- **transport**: MCP transport type (`http-sse`)
- **plane**: Architecture plane (`pm_plane` for Project Management)
- **tools_count**: Number of MCP tools provided

## Health Status Behavior

The endpoint performs a **live health check** against Leantime on each request:

1. **Healthy**: Successfully connected to Leantime API
2. **Unhealthy**: Connection failed (includes truncated error message)
3. **Unknown**: Health check not yet performed

**Performance Note**: This adds ~1-2s latency due to rate limiting. For frequently-polled discovery, consider caching the response.

## Usage Examples

### Basic Query
```bash
curl http://localhost:3015/info | jq
```

### Check Leantime Status Only
```bash
curl -s http://localhost:3015/info | jq '.leantime.status'
```

### Get MCP Connection URL
```bash
curl -s http://localhost:3015/info | jq -r '.mcp.connection.url'
```

### Automated Testing
```bash
python test_info_endpoint.py
```

## Use Cases

### 1. Service Discovery
Auto-detect Leantime Bridge configuration without hardcoded URLs:

```python
import httpx

info = httpx.get("http://localhost:3015/info").json()
sse_url = info["mcp"]["endpoints"]["sse"]
# Connect to SSE endpoint dynamically
```

### 2. Health Monitoring
Check both bridge and Leantime status:

```python
info = httpx.get("http://localhost:3015/info").json()
if info["leantime"]["status"] == "healthy":
    print("Leantime is accessible")
else:
    print(f"Leantime issue: {info['leantime']['status']}")
```

### 3. Configuration Validation
Verify environment settings before connecting:

```python
info = httpx.get("http://localhost:3015/info").json()
rate_limit = info["leantime"]["rate_limit_seconds"]
print(f"Rate limit: {rate_limit}s between requests")
```

### 4. MCP Client Auto-Configuration
Generate MCP client config from /info response:

```python
info = httpx.get("http://localhost:3015/info").json()
mcp_config = {
    "mcpServers": {
        info["name"]: {
            "command": "curl",
            "args": [info["mcp"]["endpoints"]["sse"]],
            "env": info["mcp"]["env"]
        }
    }
}
```

## Integration with Dopemux

This endpoint follows the Dopemux service discovery pattern:

1. **Standard Port**: Port 3015 (registered in `services/registry.yaml`)
2. **Standard Path**: `/info` (consistent across MCP servers)
3. **Standard Fields**: `name`, `version`, `metadata`, `mcp` sections

Other MCP servers can implement similar endpoints for unified discovery.

## Error Handling

### Bridge Not Running
```bash
$ curl http://localhost:3015/info
curl: (7) Failed to connect to localhost port 3015: Connection refused
```

**Solution**: Start leantime-bridge: `docker compose up -d leantime-bridge`

### Leantime Unhealthy
```json
{
  "leantime": {
    "status": "unhealthy: HTTPError: 500 Internal Server Error"
  }
}
```

**Solution**: Check Leantime logs: `docker logs leantime`

## Performance Considerations

- **Latency**: ~1-2s per request (includes Leantime health check)
- **Caching**: Consider caching response for 30-60s if polling frequently
- **Rate Limiting**: Respects `LEAN_TIME_RATE_LIMIT_SECONDS` setting

## Future Enhancements

- [ ] Cache health status (30s TTL)
- [ ] Add Leantime version detection
- [ ] Add uptime metrics
- [ ] Add last successful sync timestamp
- [ ] Add tool usage statistics

---

**Implemented**: 2026-02-03
**ADR**: ADR-208 (Service Discovery)
**Related**: MCP_STARTUP_FIXES.md
