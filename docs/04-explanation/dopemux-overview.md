---
id: dopemux-overview
title: Dopemux Overview
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dopemux Overview (explanation) for dopemux documentation and developer workflows.
---
# Dopemux: Unified AI Development Platform

Dopemux is an ADHD-optimized development platform that integrates AI agents for code repair, bluesky development, and system orchestration. It combines MCP tools (Zen, GPT-Researcher, Serena, Dope-Context, ConPort) with a modular architecture for seamless workflows.

## Core Components

### AI Agents
- **Vanilla Agent**: Fast iterative LLM repairs and bluesky development (ideation to documentation).
  - CLI: `dopemux code [mode] [task]`
  - Modes: repair, ideation, design, implementation, integration, testing, documentation.
  - Best for: Quick fixes, rapid prototyping.

- **Genetic Agent**: Advanced hybrid LLM + GP for complex optimization.
  - CLI: `dopemux genetic repair "complex bug"`
  - Features: Evolutionary variants, performance tuning.
  - Best for: Legacy refactoring, high-complexity problems.

### MCP Services
- **Zen**: Reasoning and planning (GPT-5-Codex for code gen).
- **GPT-Researcher**: Market research and patterns.
- **Serena**: Code analysis and dependencies.
- **Dope-Context**: Semantic search.
- **ConPort**: Knowledge graph logging.

### Infrastructure
- **Docker Compose**: All services containerized.
- **EventBus**: Real-time inter-service communication.
- **CLI**: Unified interface (`dopemux [command]`).

## Quick Start

### Installation
```bash
git clone <repo>
cd dopemux-mvp
pip install -e .
```

### Start Services
```bash
dopemux mcp start-all  # MCP tools
dopemux mcp start genetic-agent  # AI agents
```

### Basic Usage
- **Code Repair**: `dopemux code repair "bug" --file file.py`
- **Bluesky Dev**: `dopemux code develop "feature" --full-workflow`
- **Genetic Optimization**: `dopemux genetic optimize "performance" --file slow.py`

## Workflows

### Bug Repair Workflow
1. Detect bug with Serena.
2. Vanilla agent iterates repairs with Zen LLM.
3. Log to ConPort for learning.

### Bluesky Development Workflow
1. Ideation (GPT-Researcher research + Zen ideas).
2. Design (Zen planning + Serena dependencies).
3. Implementation (GPT-5-Codex code gen).
4. Integration (Serena conflict resolution).
5. Testing (pytest generation).
6. Documentation (Mkdocs/Sphinx).

## Configuration

Edit `.env`:
```
# AI Agents
VANILLA_AGENT_CONFIDENCE_THRESHOLD=0.7
GENETIC_AGENT_POPULATION_SIZE=15

# MCP URLs
ZEN_URL=http://zen:3003
GPTR_URL=http://gptr-mcp:3009
```

## Testing

```bash
pytest tests/ --cov  # Unit tests
dopemux test integration  # End-to-end
```

## Deployment

```bash
docker-compose -f docker-compose.master.yml up -d
```

Monitor: `dopemux health`.

## Architecture Diagram

```
User CLI → Dopemux CLI → AI Agents (Vanilla/Genetic)
  ↓
MCP Tools (Zen, GPT-Researcher, Serena, Dope-Context, ConPort)
  ↓
EventBus → Orchestrator → Infrastructure (Docker, Redis)
```

For detailed agent docs, see `/docs/ai-agents.md`.

This platform enables AI-assisted development at scale! 🚀
