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
docker-compose -f docker-compose.master.yml up -d desktop-commander

# Verify X11 connectivity
docker logs desktop-commander
```

## Configuration

Environment variables:
- `DISPLAY` - X11 display (default: :0)
- `PORT` - MCP server port (default: 3012)
- `XAUTHORITY` - X11 authorization file

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
