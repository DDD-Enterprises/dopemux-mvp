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
│   ├── conport/           # Knowledge graph
│   ├── conport-bridge/    # ConPort bridge
│   ├── desktop-commander/ # Desktop automation
│   ├── dopemux/           # Dopemux MCP
│   ├── gpt-researcher/    # GPT Researcher MCP
│   ├── gptr-mcp/          # GPT-Researcher MCP wrapper
│   ├── leantime-bridge/   # Leantime PM bridge
│   ├── litellm/           # LiteLLM proxy
│   ├── pal/, pal-stdio/   # PAL multi-model reasoning (formerly zen)
│   ├── serena/            # Serena LSP code intelligence
│   ├── services/          # Service Dockerfiles
│   └── docs/              # MCP server documentation
├── conport-kg/            # ConPort KG notes
├── leantime/              # Leantime image + plugins
└── postgres/              # AGE init SQL (01-init-age.sql)
```

`compose.yml` lives at the **repo root**, not in `docker/`.

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

MCP server source is in `docker/mcp-servers-source/` (symlinked from `docker/mcp-servers/`).

Do not keep a port/transport table here — it drifts. Authorities:
- **Host ports**: `services/registry.yaml`
- **Client transports/URLs**: `.mcp.json` and the transport table in root `.claude/claude.md` (AGENTS.md §12)
- **MCP catalog**: `mcp_catalog.yaml`

---

## Commands

```bash
# Smoke stack (core)
scripts/smoke_up.sh

# MCP fleet — always via the CLI, never raw `docker compose up` (AGENTS.md §12)
dopemux mcp start
dopemux mcp doctor

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
