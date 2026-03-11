# Docker Context

> **TL;DR**: Multi-stage builds, non-root users, HEALTHCHECK required. Use compose files for different stacks. MCP servers in `mcp-servers/`.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Directory Structure

```
docker/
├── mcp-servers/        # MCP server containers
│   ├── conport/        # Knowledge graph (port 3004)
│   ├── zen/            # Code analysis
│   ├── serena/         # ADHD engine
│   └── README.md       # MCP server docs
├── services/           # Service Dockerfiles
└── infrastructure/     # postgres, redis, qdrant
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

All MCP servers are in `docker/mcp-servers/`:

| Server | Port | Transport |
|--------|------|-----------|
| conport | 3004 | SSE |
| zen | - | stdio |
| serena | 8095 | HTTP |

See [`docker/mcp-servers/.claude/claude.md`](file:///Users/hue/code/dopemux-mvp/docker/mcp-servers/.claude/claude.md) for MCP-specific context.

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
