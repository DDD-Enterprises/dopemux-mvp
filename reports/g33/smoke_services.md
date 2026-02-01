# Smoke-Enabled Services

Total: 6 services

| Name | Compose Service | Port | Container Port | Health Path | Category |
|------|----------------|------|----------------|-------------|----------|
| postgres | postgres | 5432 | 5432 | N/A | infrastructure |
| redis | redis | 6379 | 6379 | N/A | infrastructure |
| qdrant | qdrant | 6333 | 6333 | / | infrastructure |
| conport | conport | 3004 | 3004 | /health | mcp |
| dopecon-bridge | dopecon-bridge | 3016 | 3016 | /health | coordination |
| task-orchestrator | task-orchestrator | 8000 | 8000 | /health | cognitive |
