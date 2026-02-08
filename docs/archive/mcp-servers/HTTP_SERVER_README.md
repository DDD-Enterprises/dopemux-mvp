---
id: HTTP_SERVER_README
title: Http_Server_Readme
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Http_Server_Readme (explanation) for dopemux documentation and developer
  workflows.
---
# Leantime MCP Bridge - HTTP/SSE Transport

## Overview

The Leantime MCP Bridge now supports **HTTP/SSE (Server-Sent Events) transport** in addition to the original stdio transport. This enables the MCP server to be accessed over HTTP, making it compatible with web-based clients, proxies, and cloud deployments.

## Architecture

### SSE Transport Pattern

The HTTP server uses **Server-Sent Events (SSE)** for bidirectional communication:

1. **SSE Stream (GET /sse)**: Server → Client messages
   - Long-lived HTTP connection
   - Server pushes messages to client as SSE events
   - First event provides the POST endpoint URL with session ID

2. **POST Endpoint (POST /messages/)**: Client → Server messages
   - Client sends JSON-RPC messages via POST
   - Session ID in query parameters links to SSE stream
   - Server responds with 202 Accepted

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sse` | GET | Establish SSE connection for server messages |
| `/messages/?session_id=<uuid>` | POST | Send client messages to server |

## Running the Server

### Docker (Recommended)

```bash
# Build and run via docker-compose
cd docker/mcp-servers
docker-compose up leantime-bridge

# Server will be available at:
# - SSE: http://localhost:3015/sse
# - POST: http://localhost:3015/messages/
```

### Standalone

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export LEANTIME_API_URL=http://leantime:80
export LEANTIME_API_TOKEN=your_token_here
export MCP_SERVER_HOST=0.0.0.0
export MCP_SERVER_PORT=3015

# Run the HTTP server
python -m leantime_bridge.http_server
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_HOST` | `0.0.0.0` | Server bind address |
| `MCP_SERVER_PORT` | `3015` | Server port |
| `LEANTIME_API_URL` | `http://leantime:80` | Leantime instance URL |
| `LEANTIME_API_TOKEN` | `""` | Leantime API authentication token |

### Docker Configuration

The server is configured in `docker-compose.yml`:

```yaml
leantime-bridge:
  environment:
    - MCP_SERVER_HOST=0.0.0.0
    - MCP_SERVER_PORT=3015
    - LEANTIME_API_URL=http://leantime:80
    - LEANTIME_API_TOKEN=${LEAN_MCP_TOKEN}
  ports:
    - "3015:3015"
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:3015/sse --head || exit 1"]
```

## Client Connection Flow

### 1. Establish SSE Connection

```python
# GET http://localhost:3015/sse
# Server responds with SSE stream
```

**First SSE Event (endpoint):**
```
event: endpoint
data: /messages/?session_id=abc123...
```

### 2. Send Initialize Request

```python
# POST http://localhost:3015/messages/?session_id=abc123...
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "client-name",
      "version": "1.0.0"
    }
  }
}
```

**Response via SSE:**
```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{...}}
```

### 3. List Tools

```python
# POST http://localhost:3015/messages/?session_id=abc123...
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

### 4. Call Tools

```python
# POST http://localhost:3015/messages/?session_id=abc123...
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "list_projects",
    "arguments": {}
  }
}
```

## Testing

### Quick Health Check

```bash
# Check if server is running
curl -I http://localhost:3015/sse

# Should return:
# HTTP/1.1 200 OK
# content-type: text/event-stream
```

### Comprehensive Test Suite

```bash
# Run the test script
python test_http_server.py

# Expected output:
# ✓ TEST PASSED: Successfully connected via SSE
# ✓ TEST PASSED: MCP initialize successful
# ✓ TEST PASSED: Successfully listed tools
```

### Manual Testing with curl

```bash
# 1. Start SSE connection (in one terminal)
curl -N http://localhost:3015/sse

# You'll see:
# event: endpoint
# data: /messages/?session_id=<uuid>

# 2. Send initialize (in another terminal, use the session_id from above)
curl -X POST "http://localhost:3015/messages/?session_id=<uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "curl-test", "version": "1.0.0"}
    }
  }'

# Watch the SSE terminal for the response
```

## Available Tools

The HTTP server exposes the same 8 Leantime integration tools:

1. **create_project** - Create new Leantime projects
2. **list_projects** - List all projects
3. **create_ticket** - Create tasks/tickets
4. **list_tickets** - List tickets from a project
5. **update_ticket** - Update ticket properties
6. **get_project_stats** - Get project statistics
7. **create_milestone** - Create project milestones
8. **sync_with_external** - Sync with external systems

## Differences from stdio Transport

| Aspect | stdio | HTTP/SSE |
|--------|-------|----------|
| **Transport** | Standard input/output | HTTP with SSE |
| **Deployment** | Process-based | Network-based |
| **Clients** | Local CLI tools | Web browsers, proxies, cloud |
| **Discovery** | Manual configuration | HTTP endpoints |
| **Load Balancing** | No | Yes (via reverse proxy) |
| **Monitoring** | Process monitoring | HTTP health checks |
| **Security** | Process isolation | HTTP headers, CORS |

## Troubleshooting

### Server Not Starting

```bash
# Check if port is in use
lsof -i :3015

# Check logs
docker logs mcp-leantime-bridge

# Verify dependencies
pip install -r requirements.txt
```

### SSE Connection Issues

```bash
# Verify SSE endpoint is accessible
curl -v http://localhost:3015/sse

# Check for proxy/firewall issues
# SSE requires long-lived connections
```

### POST Endpoint Not Found

```bash
# Ensure you're using the session ID from the SSE endpoint event
# The endpoint is dynamically provided: /messages/?session_id=<uuid>

# Verify you extracted the session ID correctly from the first SSE event
```

### Leantime API Connection

```bash
# Test Leantime API directly
curl -X POST http://leantime:80/api/jsonrpc \
  -H "Authorization: Bearer ${LEAN_MCP_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"leantime.getProjects","id":1}'

# Check environment variables
docker exec mcp-leantime-bridge env | grep LEANTIME
```

## Security Considerations

### DNS Rebinding Protection

The server includes built-in DNS rebinding protection via `TransportSecurityMiddleware`:

- Validates `Host` header matches expected values
- Validates `Origin` header for POST requests
- Prevents cross-origin attacks

### Authentication

Currently, the server does not implement its own authentication layer. It relies on:

1. **Network isolation** (Docker networks)
2. **Leantime API authentication** (bearer token)

For production deployments, consider adding:

- OAuth 2.0 authentication
- API key authentication
- Reverse proxy with authentication (nginx, Traefik)

## Performance

### Benchmarks

- **Connection establishment**: < 100ms
- **Tool call latency**: 200-500ms (depends on Leantime API)
- **Concurrent connections**: Limited by Uvicorn workers
- **Memory usage**: ~50MB base + ~10MB per connection

### Scaling

```bash
# Run with multiple workers
uvicorn leantime_bridge.http_server:starlette_app \
  --host 0.0.0.0 \
  --port 3015 \
  --workers 4

# Or use Gunicorn with Uvicorn workers
gunicorn leantime_bridge.http_server:starlette_app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:3015
```

## Future Enhancements

- [ ] WebSocket transport option (full bidirectional)
- [ ] OAuth 2.0 authentication
- [ ] Prometheus metrics endpoint
- [ ] Request rate limiting
- [ ] Connection pooling for Leantime API
- [ ] Structured logging with request tracing

## References

- [MCP SSE Transport Spec](https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/sse.py)
- [Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Leantime API Documentation](https://docs.leantime.io/developers/api/)
- [Starlette Framework](https://www.starlette.io/)
- [Uvicorn ASGI Server](https://www.uvicorn.org/)
