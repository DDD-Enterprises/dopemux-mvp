# Serena MCP Server

**Category**: MCP Server  
**Status**: Experimental  
**Purpose**: ADHD-optimized code navigation intelligence

## Overview

Serena is an MCP server providing intelligent code navigation and analysis optimized for ADHD developers. Features include semantic search, AST analysis, and context-aware code browsing.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d serena

# Check logs
docker logs mcp-serena
```

## Configuration

Environment variables:
- `PORT` - MCP server port (default: 3001)
- `LOG_LEVEL` - Logging verbosity (default: INFO)

## Features

- **Semantic Code Search** - Find code by meaning, not just keywords
- **AST Analysis** - Deep code structure understanding
- **ADHD-Optimized** - Complexity scoring and progressive disclosure
- **Multi-Language** - Python, JavaScript, TypeScript, Rust, Go, Java

## Documentation

See [docs/03-reference/systems/adhd-intelligence/](../../../docs/03-reference/systems/adhd-intelligence/) for detailed documentation.

## Development

```bash
# Run locally
cd docker/mcp-servers/serena
python wrapper.py
```
