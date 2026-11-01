# Services Development Context

> **TL;DR**: Build ADHD-friendly microservices. Register in `registry.yaml`, add `/health` endpoint, use FastAPI. Check existing services before creating new ones.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Before Creating a Service

1. **Check if it exists**: Search `services/` first
2. **Register**: Add to `services/registry.yaml`
3. **Port assignment**: Use next available in registry
4. **Health check**: Required for all HTTP services

---

## Service Registry

All services must be registered in [`services/registry.yaml`](../registry.yaml) (a **list**; schema in the file header):

```yaml
services:
  - name: my-service
    port: 30XX            # host port
    container_port: 8000  # optional, defaults to port
    health_path: /health
    enabled_in_smoke: false
    category: cognitive   # infrastructure|mcp|coordination|cognitive
    description: ...
```

---

## Key Services

Host ports from `registry.yaml` (verify there before relying on them):

| Service | Host port | Purpose |
|---------|-----------|---------|
| conport | 3004 HTTP / 3005 MCP (SSE) | Knowledge graph, memory (source: `docker/mcp-servers-source/conport/`) |
| dopecon-bridge | 3016 | Event routing |
| task-orchestrator | 8000 | ADHD-aware task mgmt (the MCP singleton is separate, `:7890`) |
| adhd-engine | 3025 (8095 in-container) | Energy / attention / cognitive-load engine |
| serena | 3006 | LSP code intelligence |

---

## Service Template

```python
# services/[name]/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting service")
    yield
    logger.info("🛑 Shutting down")

app = FastAPI(title="[Service]", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "[name]"}
```

---

## Docker Guidelines

- Use `docker/` for Dockerfiles
- Add to appropriate compose file:
  - `compose.yml` - Canonical stack (use `scripts/smoke_up.sh` for core smoke subset)
- Include HEALTHCHECK in Dockerfile

---

## Existing Service Categories

```
services/
├── task-orchestrator/    # ADHD-aware coordination
├── dopecon-bridge/       # Event routing
├── adhd_engine/          # ADHD engine
├── dope-context/, dope-memory/, serena/, dcp-readonly-facade/, ...
└── (~21 service dirs total — `ls services/`; ConPort source is in docker/mcp-servers-source/)
```

Always check existing services before creating duplicates.

## Documentation Sync

When service behavior changes, run the PR docgen sync workflow so user/dev/devops/product docs stay aligned:

- Core + wrappers: `templates/skills/pr-docgen-sync*/`
- Installer: `python scripts/skills/sync_repo_skills.py --family pr-docgen-sync`
- Baseline: `main...HEAD`
