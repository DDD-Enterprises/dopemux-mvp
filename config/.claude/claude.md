# Configuration Context

> **TL;DR**: Pydantic settings with env var binding. profiles/ for ADHD, mcp/ for MCP servers. Validate early, fail fast.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Directory Structure

```
config/
├── profiles/          # ADHD profiles (see below)
├── env/               # Environment variable definitions
├── orchestrator/      # Orchestrator policy files
├── preflight/         # Pre-flight check configs
├── instructions/      # Instruction templates
├── mobile/            # Mobile-specific config
├── pr_merge_specialist/   # PR merge policy config
├── docs_hygiene/      # Docs hygiene rules
├── extraction_hygiene/    # Extraction rules
├── repo_hygiene/      # Repo hygiene rules
├── dotfiles/          # Dotfile templates
├── pricing.yaml       # LLM cost/pricing data
└── runtime_authority_manifest.json  # Runtime authority config
```

Note: `.claude.json` lives at the **repo root**, not inside `config/`.

---

## Key Files

| File | Purpose |
|------|---------|
| `../.claude.json` | MCP server configuration (repo root) |
| `config/profiles/*.yaml` | ADHD energy profiles |
| `config/pricing.yaml` | LLM model cost data |
| `config/runtime_authority_manifest.json` | Runtime authority config |
| `.env.example` | Environment template (repo root) |

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
- `CHEAPERINFERENCE_API_KEY` - LLM access
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `QDRANT_URL` - Vector database

---

## ADHD Profiles

Profiles in `config/profiles/`:
- `adhd-default.yaml` - Default ADHD-optimized settings
- `safe.yaml` - Conservative / low-risk mode
- `dangerous.yaml` - Full capabilities, elevated risk tolerance
- `python-ml.yaml` - Python/ML focused environment
- `web-dev.yaml` - Web development environment
- `workflow-executor.yaml` - Workflow automation mode
- `workflow-manager.yaml` - Workflow management mode

---

## Validation

```python
# Required: Fail fast on invalid config
config = AppConfig()  # Raises ValidationError if missing required

# Clear error messages
❌ Missing 'database_url' - check DATABASE_URL env var
```