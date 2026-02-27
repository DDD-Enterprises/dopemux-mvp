# Desktop Commander MCP Server

**Category**: MCP Server  
**Status**: Production  
**Port**: 3012  
**Purpose**: Desktop automation for ADHD-optimized workflows

## Overview

Desktop Commander provides desktop automation capabilities through MCP, enabling window management, screenshots, and keyboard automation for seamless developer workflows.

## Quick Start

```bash
# Start via Docker Compose
cd docker/mcp-servers
docker compose up -d --build desktop-commander

# Verify X11 connectivity
docker logs dopemux-mcp-desktop-commander
```

## Configuration

Environment variables:
- `DISPLAY` - X11 display (default: :0)
- `MCP_SERVER_HOST` - MCP server bind address (default: 127.0.0.1 for local, 0.0.0.0 in Docker)
- `MCP_SERVER_PORT` - MCP server port (default: 3012)
- `DESKTOP_COMMANDER_API_KEY` - Optional API key for authentication (highly recommended if host is 0.0.0.0)
- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins
- `XAUTHORITY` - X11 authorization file

## Security

Desktop Commander includes several security features to protect your system:
- **Host Binding**: Defaults to `127.0.0.1` when run locally to prevent unauthorized network access.
- **Authentication**: Supports API key authentication via the `X-API-Key` header.
- **CORS**: Configurable CORS policy to restrict browser-based access.

To enable authentication, set the `DESKTOP_COMMANDER_API_KEY` environment variable and include it in your requests:
```bash
curl -H "X-API-Key: your-secret-key" http://localhost:3012/mcp
```

## MCP Tools

- `screenshot` - Capture desktop state
- `window_list` - List all open windows
- `focus_window` - Auto-focus specific windows
- `type_text` - Automated text input

## ADHD Integration

Desktop Commander enables sub-2-second context switching:
- Serena → Desktop Commander → Auto-focus window
- Visual context preservation via screenshots
- Automatic window focus after code navigation

## Documentation

- [CONNECTION_GUIDE.md](CONNECTION_GUIDE.md) - Setup and troubleshooting
- [DESKTOP_COMMANDER_VALIDATION.md](DESKTOP_COMMANDER_VALIDATION.md) - Validation results

## Development

```bash
# Run locally
cd docker/mcp-servers/desktop-commander
python integration_bridge_connector.py
```
