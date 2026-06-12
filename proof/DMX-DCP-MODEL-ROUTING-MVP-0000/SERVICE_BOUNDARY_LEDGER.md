# DMX-DCP-MODEL-ROUTING-MVP-0000 — SERVICE_BOUNDARY_LEDGER.md

## Service Boundary Ledger (from services/registry.yaml + compose.yml)

### Infrastructure Services

| Service | Port | Health | Category | Compose Name | Smoke | Evidence |
|---------|------|--------|----------|--------------|-------|----------|
| postgres (AGE) | 5432 | pg_isready | infrastructure | postgres | Yes | compose.yml + registry.yaml |
| redis-events | 6379 | redis-cli ping | infrastructure | redis-events | No | compose.yml + registry.yaml |
| redis-primary | 6380 | redis-cli ping | infrastructure | redis-primary | No | compose.yml + registry.yaml |
| qdrant | 6333 | / | infrastructure | mcp-qdrant | Yes | compose.yml + registry.yaml |
| litellm | 4000 | /health (Bearer) | infrastructure | litellm | No | compose.yml + registry.yaml |

### Coordination Services

| Service | Port | Health | Category | Compose Name | Smoke | Evidence |
|---------|------|--------|----------|--------------|-------|----------|
| dopecon-bridge | 3016 | /health | coordination | dopecon-bridge | Yes | compose.yml + registry.yaml |
| leantime-bridge | 3015 | /health | coordination | leantime-bridge | No | registry.yaml |
| leantime | 8080 | / | coordination | leantime | No | compose.yml + registry.yaml |
| webhook-receiver | 8790 | /healthz | coordination | webhook-receiver | No | registry.yaml |

### MCP Services

| Service | Port | Health | Category | Compose Name | Smoke | Evidence |
|---------|------|--------|----------|--------------|-------|----------|
| conport-http | 3004 | /health | mcp | conport | Yes | compose.yml + registry.yaml |
| conport-mcp | 3005 | /health | mcp | conport | No | compose.yml + registry.yaml |
| pal | 3003 | exit 0 | mcp | pal | No | compose.yml + registry.yaml |
| serena | 3006 | /health | mcp | serena | No | registry.yaml |
| gpt-researcher | 3009 | /health | mcp | gptr-mcp | No | registry.yaml |
| dope-context | 3010 | /health | mcp | dope-context | No | compose.yml + registry.yaml |
| exa | 3011 | /health | mcp | exa | No | registry.yaml |
| desktop-commander | 3012 | /health | mcp | desktop-commander | No | registry.yaml |
| dope-memory | 3020 | /health | mcp | dope-memory | Yes | registry.yaml |

### Cognitive Services

| Service | Port | Health | Category | Compose Name | Smoke | Evidence |
|---------|------|--------|----------|--------------|-------|----------|
| task-orchestrator | 8000 | /health | cognitive | task-orchestrator | Yes | registry.yaml |
| adhd-engine | 3025/8095 | /health | cognitive | adhd-engine | No | registry.yaml |

**Total Services**: 22
**Smoke Stack**: 7 (postgres, qdrant, dopecon-bridge, conport-http, dope-memory, task-orchestrator)
**Health Contract Exceptions**: conport (PORT/LOG_LEVEL/ENVIRONMENT/HEALTH_CHECK_PATH/SERVICE_NAME), task-orchestrator (DATABASE_URL)
