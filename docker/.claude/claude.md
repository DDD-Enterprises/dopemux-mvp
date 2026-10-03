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

# Full stack (MCP servers, bridge, orchestrator, app services) — always via the CLI,
# never raw `docker compose up` (AGENTS.md §12). start-all's --verify only runs when
# scripts/start-all.sh exists (absent in a clean checkout, where start-all falls back to
# plain compose startup without checks). There is no single full-stack health gate:
#   - `dopemux mcp doctor` = sidecar/config diagnostics (conport, dope-memory, task-orchestrator only)
#   - `scripts/smoke_up.sh` runs tools/smoke_runtime_gate.py (container/port/HTTP checks)
#     for the `enabled_in_smoke` services in services/registry.yaml only
#   - other services: probe their `health_path` from services/registry.yaml
dopemux mcp start-all

# Repo sidecars only (assumes shared infrastructure is already up):
#   conport, dope-memory -> worktree-scoped containers
#   task-orchestrator    -> host-wide wrapper-singleton on :7890, one active project at a time
#                           (not isolated per project; see AGENTS.md §12.6)
dopemux mcp start
dopemux mcp doctor      # sidecar/config diagnostics for the three services above

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
