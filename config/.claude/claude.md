# Configuration Context

> **TL;DR**: Pydantic settings with env var binding. profiles/ for ADHD, mcp/ for MCP servers. Validate early, fail fast.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Directory Structure

```
config/
├── profiles/          # ADHD profiles (low/medium/high energy)
├── mcp/               # MCP server configurations
├── routing/           # Event routing rules
├── logging/           # Logging configurations
└── environments/      # dev/staging/prod settings
```

---

## Key Files

| File | Purpose |
|------|---------|
| `.claude.json` | MCP server configuration |
| `services/registry.yaml` | Service ports/health |
| `config/profiles/*.yaml` | ADHD energy profiles |
| `.env.example` | Environment template |

---

## Settings Pattern

```python
from pydantic import BaseSettings, Field

class AppConfig(BaseSettings):
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    database_url: str = Field(..., env="DATABASE_URL")
    
    class Config:
        env_file = ".env"
```

---

## Environment Variables

Key variables (see `.env.example`):
- `OPENROUTER_API_KEY` - LLM access
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `QDRANT_URL` - Vector database

---

## ADHD Profiles

Profiles in `config/profiles/`:
- `low_energy.yaml` - Minimal features, simple tasks
- `medium_energy.yaml` - Standard operation
- `high_energy.yaml` - Full features, complex tasks

---

## Validation

```python
# Required: Fail fast on invalid config
config = AppConfig()  # Raises ValidationError if missing required

# Clear error messages
❌ Missing 'database_url' - check DATABASE_URL env var
```