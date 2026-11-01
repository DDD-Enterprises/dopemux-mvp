# Configuration Context

> **TL;DR**: Pydantic settings with env var binding. profiles/ for ADHD, mcp/ for MCP servers. Validate early, fail fast.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Directory Structure

```
config/
├── ai/                # model-routing.policy.yaml (advisory model lanes)
├── audit/             # Audit configs
├── commandcode/       # Normalized agent/persona catalog (generated)
├── dcp/               # DCP facade config
├── pr_steward/        # PR steward config
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

Note: MCP client config is `.mcp.json` at the **repo root** (not `.claude.json`, which is an empty `{}`).

---

## Key Files

| File | Purpose |
|------|---------|
| `.mcp.json` | MCP client configuration (repo root) |
| `config/ai/model-routing.policy.yaml` | Model routing lanes (pinned by `tests/test_model_routing_policy.py`) |
| `config/profiles/*.yaml` | ADHD energy profiles |
| `config/pricing.yaml` | LLM model cost data |
| `config/runtime_authority_manifest.json` | Runtime authority config |
| `.env.example` | Environment template (repo root) |

---

## Settings Pattern

```python
# Pydantic v2 (repo pins pydantic>=2.7 + pydantic-settings); `pydantic.BaseSettings` no longer exists
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    environment: str = "development"   # reads ENVIRONMENT
    debug: bool = False                # reads DEBUG
    database_url: str                  # reads DATABASE_URL (required)
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