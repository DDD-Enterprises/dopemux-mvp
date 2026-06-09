# Docker Context

> **TL;DR**: Multi-stage builds, non-root users, HEALTHCHECK required. Use compose files for different stacks. MCP servers in `mcp-servers/`.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Directory Structure

```
docker/
├── mcp-servers/           # Symlink → mcp-servers-source/
├── mcp-servers-source/    # Actual MCP server source (editable)
│   ├── claude-context/    # Claude context server
│   ├── conport/           # Knowledge graph (port 3004)
│   ├── conport-bridge/    # ConPort bridge
│   ├── desktop-commander/ # Desktop automation
│   ├── dopemux/           # Dopemux MCP
│   ├── exa/               # Exa search MCP
│   ├── gpt-researcher/    # GPT Researcher MCP
│   ├── gptr-mcp/          # GPT-Researcher MCP wrapper
│   ├── leantime-bridge/   # Leantime PM bridge
│   ├── litellm/           # LiteLLM proxy
│   ├── pal/               # PAL multi-model reasoning (formerly zen)
│   ├── serena/            # Serena LSP code intelligence
│   ├── services/          # Service Dockerfiles
│   └── docs/              # MCP server documentation
├── services/              # Service Dockerfiles
└── infrastructure/        # postgres, redis, qdrant
```

---

## Compose Files

| File | Purpose | Use When |
|------|---------|----------|
| `compose.yml` | Canonical stack | Full development and smoke subsets |

---

## Dockerfile Standards

```dockerfile
FROM python:3.11-slim as base
RUN useradd --create-home app
WORKDIR /app

# Always include health check
HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8000/health || exit 1

USER app
CMD ["uvicorn", "main:app"]
```

---

## MCP Servers

MCP server source is in `docker/mcp-servers-source/` (symlinked from `docker/mcp-servers/`):

| Server | Port | Transport |
|--------|------|-----------|
| conport | 3004 | SSE |
| pal | - | stdio |
| serena | 8095 | HTTP |
| desktop-commander | 3012 | stdio |
| exa | - | stdio |
| gpt-researcher | 3009 | HTTP |
| litellm | varies | HTTP |
| leantime-bridge | - | stdio |

See `docker/mcp-servers-source/.claude/claude.md` for MCP-specific context.

---

## Commands

```bash
# Smoke stack (core)
scripts/smoke_up.sh

# Full stack
docker compose -f compose.yml up -d

# Build specific service
docker compose -f compose.yml build my-service

# Health check
docker compose -f compose.yml ps
```

## Documentation Sync

When docker/compose changes affect runtime behavior or ports, trigger the PR docgen sync workflow:

- Skill templates: `templates/skills/pr-docgen-sync*/`
- Installer: `python scripts/skills/sync_repo_skills.py --family pr-docgen-sync`
- Baseline: `main...HEAD`
