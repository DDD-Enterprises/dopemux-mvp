# Context7 MCP Server

**Category**: MCP Server  
**Status**: Production  
**Purpose**: Context management and retrieval

## Overview

Context7 provides intelligent context management for AI-assisted development, tracking conversation history, decisions, and code context across sessions.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d context7

# Verify running
curl http://localhost:3007/health
```

## Configuration

Environment variables:
- `CONTEXT7_API_KEY` - API key for Context7 service
- `PORT` - MCP server port (default: 3007)

## Features

- **Session Management** - Track conversations across sessions
- **Decision Logging** - Automatic decision capture
- **Context Retrieval** - Intelligent context suggestions
- **Cross-Session Memory** - Maintain continuity

## Documentation

See Context7 official documentation for API details.
