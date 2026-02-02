# Claude Context MCP Server

**Category**: MCP Server  
**Status**: Experimental  
**Purpose**: Claude Code integration and context management

## Overview

Claude Context provides specialized context management for Claude Code interactions, maintaining conversation history and project context optimized for ADHD workflows.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d claude-context

# Check status
docker logs mcp-claude-context
```

## Configuration

Environment variables:
- `PORT` - MCP server port (default: 3014)
- `LOG_LEVEL` - Logging verbosity (default: INFO)
- `ANTHROPIC_API_KEY` - Claude API key (optional)

## Features

- **Conversation History** - Track Claude Code sessions
- **Context Preservation** - Maintain project context
- **ADHD-Optimized** - Progressive disclosure of context
- **Session Recovery** - Resume previous conversations

## Documentation

See Claude Code documentation for integration details.

## Development

```bash
# Run locally
cd docker/mcp-servers/claude-context
# Setup and run instructions TBD
```
