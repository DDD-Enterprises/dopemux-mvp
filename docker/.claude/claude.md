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
| `docker-compose.smoke.yml` | Core services only | Testing basics |
| `docker-compose.master.yml` | Full stack | Full development |
| `docker-compose.monitoring.yml` | Grafana/Prometheus | Observability |

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
docker-compose -f docker-compose.smoke.yml up

# Full stack
docker-compose -f docker-compose.master.yml up

# Build specific service
docker-compose build my-service

# Health check
docker-compose ps
```