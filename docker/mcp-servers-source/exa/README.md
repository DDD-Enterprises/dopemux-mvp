# Exa MCP Server

**Category**: MCP Server  
**Status**: Production  
**Port**: 3008  
**Purpose**: Neural search for web content

## Overview

Exa provides AI-powered semantic web search through MCP, enabling intelligent content discovery and research automation.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d exa

# Verify running
docker logs mcp-exa
```

## Configuration

Environment variables:
- `EXA_API_KEY` - API key for Exa service (required)
- `PORT` - MCP server port (default: 3008)
- `LOG_LEVEL` - Logging verbosity (default: INFO)

## MCP Tools

- `search` - Semantic web search
- `find_similar` - Find content similar to URL
- `get_contents` - Extract clean content from URLs

## Use Cases

- **Research** - Find relevant technical documentation
- **Code Examples** - Discover similar implementations
- **Documentation** - Locate API references and guides

## Documentation

See [exa.ai](https://exa.ai) for API documentation.

## Development

```bash
# Test search
curl -X POST http://localhost:3008/search \
  -H "Content-Type: application/json" \
  -d '{"query": "ADHD-friendly UI patterns"}'
```
