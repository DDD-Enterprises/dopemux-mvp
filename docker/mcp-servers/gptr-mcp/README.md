# GPT Researcher MCP Server

## Overview

The GPT Researcher MCP server provides autonomous research capabilities through the Model Context Protocol. It wraps the upstream [gptr-mcp](https://github.com/assafelovic/gptr-mcp) server with an HTTP health check layer for Docker orchestration.

## Architecture

### Hybrid Transport Design

This implementation uses a **hybrid approach**:

1. **Upstream Server (stdio mode)**: The GPT Researcher MCP server runs in `stdio` mode for compatibility with Claude Desktop and other stdio-based clients
2. **HTTP Wrapper**: A lightweight HTTP server provides health check endpoints for Docker orchestration

```
┌─────────────────────────────────────┐
│   HTTP Wrapper (port 3009)          │
│   - /health (Docker healthcheck)    │
│   - /info (Server information)      │
└──────────────┬──────────────────────┘
               │ spawns & monitors
               ▼
┌─────────────────────────────────────┐
│   GPT Researcher MCP (stdio)        │
│   - Autonomous research              │
│   - Web search & synthesis           │
│   - Report generation                │
└─────────────────────────────────────┘
```

### Why This Architecture?

**Problem**: The upstream gptr-mcp server runs in stdio mode (for Claude Desktop), but Docker needs HTTP health checks.

**Solution**: HTTP wrapper that:
- Spawns the upstream server in stdio mode
- Provides `/health` endpoint checking if upstream process is alive
- Keeps the server compatible with Claude Desktop stdio transport
- Enables Docker healthcheck and monitoring

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_PORT` | `3009` | HTTP wrapper port |
| `GPTR_UPSTREAM_PORT` | `3015` | (Reserved, not used in stdio mode) |
| `OPENAI_API_KEY` | - | OpenAI API key (required) |
| `TAVILY_API_KEY` | - | Tavily search API key (required) |

### Docker Deployment

```bash
# Build and run via docker-compose
cd docker/mcp-servers
docker-compose up gptr-mcp

# Check health
curl http://localhost:3009/health
```

## Endpoints

### HTTP Wrapper Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check for Docker (returns process status) |
| `/` or `/info` | GET | Server information and mode details |

### Health Check Response

```json
{
  "status": "healthy",
  "wrapper_port": 3009,
  "upstream_mode": "stdio",
  "upstream_running": true,
  "upstream_pid": 42
}
```

## MCP Communication

### For Claude Desktop (stdio)

The upstream server runs in stdio mode. To use it with Claude Desktop, configure it in your MCP settings:

```json
{
  "mcpServers": {
    "gptr-mcp": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-gptr-mcp", "python", "/app/gptr-mcp/server.py"]
    }
  }
}
```

### For Direct stdio Access

```bash
# Interactive stdio session
docker exec -i mcp-gptr-mcp python /app/gptr-mcp/server.py
```

## Troubleshooting

### Container Not Starting

```bash
# Check logs
docker logs mcp-gptr-mcp

# Verify API keys are set
docker exec mcp-gptr-mcp env | grep -E "OPENAI|TAVILY"
```

### Health Check Failing

```bash
# Test health endpoint directly
curl -v http://localhost:3009/health

# Check if wrapper is running
docker exec mcp-gptr-mcp ps aux | grep python

# Check upstream process status
docker exec mcp-gptr-mcp ps aux | grep server.py
```

### Upstream Server Crashes

```bash
# Check upstream logs (captured by wrapper)
docker logs mcp-gptr-mcp | grep "server.py"

# Restart container
docker-compose restart gptr-mcp
```

## Files

### Key Files

- **Dockerfile**: Builds container with upstream gptr-mcp + HTTP wrapper
- **gptr_http_wrapper.py**: HTTP server providing health checks
- **.env.template**: Environment variable template

### Directory Structure (in container)

```
/app/
├── gptr-mcp/              # Cloned upstream repository
│   ├── server.py          # Main GPT Researcher MCP server (stdio)
│   ├── requirements.txt   # Upstream dependencies
│   └── ...
├── gptr_http_wrapper.py   # HTTP wrapper (our code)
├── .env                   # Environment configuration
├── logs/                  # Log directory
└── data/                  # Data directory
```

## Comparison: stdio vs HTTP

| Aspect | stdio Mode (Current) | HTTP/SSE Mode |
|--------|---------------------|---------------|
| **Transport** | stdin/stdout | HTTP with SSE |
| **Claude Desktop** | ✅ Native support | ⚠️ Requires configuration |
| **Docker Health** | ⚠️ Requires wrapper | ✅ Native HTTP checks |
| **Network Access** | ❌ Local only | ✅ Network-accessible |
| **Deployment** | Process-based | Network-based |

## Future Enhancements

Potential improvements:

- [ ] Full HTTP/SSE transport (similar to Leantime MCP)
- [ ] WebSocket support for bidirectional communication
- [ ] REST API for research job submission
- [ ] Webhook notifications for research completion
- [ ] Prometheus metrics endpoint
- [ ] Research job queueing and management

## Resources

- [Upstream gptr-mcp repository](https://github.com/assafelovic/gptr-mcp)
- [FastMCP Framework](https://gofastmcp.com)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [GPT Researcher](https://github.com/assafelovic/gpt-researcher)

## License

Wrapper code: MIT (Dopemux project)
Upstream gptr-mcp: See [upstream repository](https://github.com/assafelovic/gptr-mcp)
