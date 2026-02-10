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

All services must be registered in [`services/registry.yaml`](file:///Users/hue/code/dopemux-mvp/services/registry.yaml):

```yaml
services:
  my-service:
    name: my-service
    port: 8XXX
    transport: http
    health_endpoint: /health
    category: cognitive  # infrastructure|mcp|coordination|cognitive
```

---

## Key Services

| Service | Port | Purpose |
|---------|------|---------|
| conport | 3004 | Knowledge graph, memory |
| dopecon-bridge | 3016 | Event routing |
| task-orchestrator | 8000 | ADHD-aware task mgmt |
| adhd-engine | 8095 | Serena ADHD accommodations |

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
  - `docker-compose.smoke.yml` - Core services
  - `docker-compose.master.yml` - Full stack
- Include HEALTHCHECK in Dockerfile

---

## Existing Service Categories

```
services/
├── task-orchestrator/    # ADHD-aware coordination
├── dopecon-bridge/       # Event routing
├── orchestrator/         # Tmux layout management
├── adhd_engine/          # Serena ADHD engine
├── conport/              # (in docker/mcp-servers/)
└── [50+ more services]
```

Always check existing services before creating duplicates.