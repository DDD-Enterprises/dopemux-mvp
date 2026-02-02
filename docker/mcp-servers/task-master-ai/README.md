# Task Master AI MCP Server

**Category**: MCP Server  
**Status**: Experimental  
**Purpose**: AI-powered task decomposition and orchestration

## Overview

Task Master AI provides intelligent task decomposition and orchestration through MCP, breaking down complex tasks into ADHD-friendly subtasks with complexity scoring.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d task-master-ai

# Verify running
docker logs mcp-task-master-ai
```

## Configuration

Environment variables:
- `PORT` - MCP server port (default: 3015)
- `OPENROUTER_API_KEY` - OpenRouter API key for LLM access
- `LOG_LEVEL` - Logging verbosity (default: INFO)

## MCP Tools

- `decompose_task` - Break complex task into subtasks
- `score_complexity` - Rate task complexity (0.0-1.0)
- `suggest_order` - Recommend optimal task sequence
- `estimate_time` - Estimate task duration

## ADHD Optimization

- **Complexity Scoring** - 0.0-1.0 scale for cognitive load
- **Progressive Decomposition** - Break tasks to ADHD-safe size
- **Energy Matching** - Suggest tasks based on energy level
- **Context Preservation** - Maintain task relationships

## Documentation

See task orchestrator documentation for integration patterns.

## Development

```bash
# Test task decomposition
curl -X POST http://localhost:3015/decompose \
  -H "Content-Type: application/json" \
  -d '{"task": "Implement authentication system"}'
```
