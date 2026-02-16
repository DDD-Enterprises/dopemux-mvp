---
id: service_env_contract
title: Service_Env_Contract
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Service_Env_Contract (reference) for dopemux documentation and developer
  workflows.
---
# Service Environment Contract

**Version**: 1.0
**Status**: Active (G33)
**Last Updated**: 2026-02-01

## Purpose

This contract defines the mandatory and optional environment variables that all Dopemux services must support. It ensures consistent configuration, deployment, and observability across the service ecosystem.

## Scope

- **Applies To**: All services with `enabled_in_smoke: true` in `services/registry.yaml`
- **Exceptions**: Only via explicit `env_contract_exceptions` in registry entry
- **Enforcement**: Architecture tests (`tests/arch/test_service_env_contract.py`)
- **Validation**: Environment drift scanner (`tools/env_drift_scan.py`)

## Mandatory Environment Variables

All smoke-enabled services MUST support these environment variables:

### Core Configuration

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `PORT` \| integer \| (none) \| Container-internal HTTP port \| `8080` |
| `LOG_LEVEL` \| string \| `INFO` \| Logging verbosity level \| `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `ENVIRONMENT` \| string \| `dev` \| Deployment environment \| `dev`, `staging`, `prod` |

### Observability

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `HEALTH_CHECK_PATH` \| string \| `/health` \| Health check endpoint path \| `/health`, `/api/health` |
| `METRICS_ENABLED` \| boolean \| `false` \| Enable Prometheus metrics \| `true`, `false` |
| `METRICS_PORT` \| integer \| `9090` \| Prometheus metrics port \| `9090` |

### Service Identity

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `SERVICE_NAME` \| string \| (auto-detect) \| Canonical service name \| `conport`, `dopecon-bridge` |
| `SERVICE_VERSION` \| string \| (auto-detect) \| Semantic version \| `1.0.0`, `2.1.3` |

## Category-Specific Variables

### Infrastructure Services (`category: infrastructure`)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_CONNECTIONS` \| integer \| `100` | Maximum concurrent connections |
| `CONNECTION_TIMEOUT` \| integer \| `30` | Connection timeout (seconds) |

### MCP Services (`category: mcp`)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MCP_SERVER_PORT` | integer | (same as PORT) | MCP protocol port |
| `MCP_TRANSPORT` \| string \| `stdio` \| Transport protocol (`stdio`, `sse`) |

### Coordination Services (`category: coordination`)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | string | (required) | Redis connection string |
| `EVENT_BUS_ENABLED` \| boolean \| `true` | Enable event bus integration |

### Cognitive Services (`category: cognitive`)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | string | (required) | PostgreSQL connection string |
| `REDIS_URL` | string | (required) | Redis connection string |
| `CONPORT_URL` | string | (required) | ConPort API base URL |

## Implementation Requirements

### 1. Environment Variable Loading

Services MUST load env vars at startup using this pattern:

```python
import os
from typing import Optional

class ServiceConfig:
    """Unified service configuration."""

    def __init__(self):
        # Mandatory core vars
        self.port = int(os.getenv("PORT", "8080"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.environment = os.getenv("ENVIRONMENT", "dev")

        # Observability
        self.health_check_path = os.getenv("HEALTH_CHECK_PATH", "/health")
        self.metrics_enabled = os.getenv("METRICS_ENABLED", "false").lower() == "true"
        self.metrics_port = int(os.getenv("METRICS_PORT", "9090"))

        # Service identity
        self.service_name = os.getenv("SERVICE_NAME", self._detect_service_name())
        self.service_version = os.getenv("SERVICE_VERSION", "1.0.0")

    def _detect_service_name(self) -> str:
        """Auto-detect service name from directory."""
        import pathlib
        return pathlib.Path.cwd().name

    def validate(self):
        """Validate required configuration."""
        if self.port <= 0 or self.port > 65535:
            raise ValueError(f"Invalid PORT: {self.port}")

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid LOG_LEVEL: {self.log_level}")

        if self.environment not in ["dev", "staging", "prod"]:
            raise ValueError(f"Invalid ENVIRONMENT: {self.environment}")

# Usage in service
config = ServiceConfig()
config.validate()
```

### 2. Logging Configuration

Services MUST configure logging based on `LOG_LEVEL`:

```python
import logging
import sys

def setup_logging(config: ServiceConfig):
    """Configure logging from environment."""
    log_level = getattr(logging, config.log_level.upper())

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(config.service_name)
    logger.info(f"🚀 Starting {config.service_name} v{config.service_version}")
    logger.info(f"📊 Environment: {config.environment}")
    logger.info(f"🔧 Port: {config.port}")
    logger.info(f"📝 Log Level: {config.log_level}")

    return logger
```

### 3. Health Check Endpoint

Services MUST expose a health check endpoint at `HEALTH_CHECK_PATH`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str
    version: str
    environment: str

app = FastAPI()

@app.get(config.health_check_path)
async def health_check() -> HealthResponse:
    """Standard health check endpoint."""
    return HealthResponse(
        service=config.service_name,
        version=config.service_version,
        environment=config.environment
    )
```

### 4. Metrics Endpoint (Optional)

If `METRICS_ENABLED=true`, services SHOULD expose Prometheus metrics:

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

if config.metrics_enabled:
    # Define metrics
    request_count = Counter('http_requests_total', 'Total HTTP requests')
    request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(
            content=generate_latest(),
            media_type="text/plain"
        )
```

## Exceptions Process

Services may request exceptions to mandatory env vars via `services/registry.yaml`:

```yaml
services:
- name: postgres
    port: 5432
    enabled_in_smoke: true
    category: infrastructure
    env_contract_exceptions:
- variable: PORT
        reason: "PostgreSQL uses internal port 5432, controlled by POSTGRES_PORT"
- variable: LOG_LEVEL
        reason: "PostgreSQL logging configured via postgresql.conf"
```

**Exception Review**: All exceptions require architectural review and must include:
1. Variable name
1. Justification (why exception needed)
1. Alternative mechanism (how config is handled)

## Validation

### Static Validation

Run the env drift scanner to detect violations:

```bash
python tools/env_drift_scan.py
```

Output includes:
- Services missing mandatory env vars
- Services with undocumented env vars
- Recommended fixes

### Dynamic Validation

Architecture tests enforce the contract:

```bash
pytest tests/arch/test_service_env_contract.py -v
```

Tests verify:
- Smoke-enabled services load mandatory env vars
- Services respect exceptions defined in registry
- Health endpoints are accessible
- Logging configuration works

## Migration Guide

### For Existing Services

1. **Add ServiceConfig class** to service entry point
1. **Update startup** to load and validate config
1. **Configure logging** from LOG_LEVEL env var
1. **Expose health endpoint** at HEALTH_CHECK_PATH
1. **Update Dockerfile** to accept env vars as ARG/ENV
1. **Update docker-compose** to pass env vars

### Example Migration (task-orchestrator)

**Before**:
```python
# services/task-orchestrator/server.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
```

**After**:
```python
# services/task-orchestrator/server.py
import uvicorn
from config import ServiceConfig, setup_logging

config = ServiceConfig()
config.validate()
logger = setup_logging(config)

if __name__ == "__main__":
    logger.info(f"🚀 Starting on port {config.port}")
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=config.port,
        log_level=config.log_level.lower()
    )
```

**Dockerfile**:
```dockerfile
# Accept env vars as build args
ARG PORT=8000
ARG LOG_LEVEL=INFO
ARG ENVIRONMENT=dev

# Set as environment variables
ENV PORT=${PORT}
ENV LOG_LEVEL=${LOG_LEVEL}
ENV ENVIRONMENT=${ENVIRONMENT}

CMD ["python", "server.py"]
```

## Compliance Roadmap

### Phase 1: Documentation (Complete)
- ✅ Define unified contract
- ✅ Create validation tools
- ✅ Write migration guide

### Phase 2: Smoke Stack Services (G33)
- 🔄 Migrate 6 smoke-enabled services:
- postgres (exception: uses POSTGRES_PORT)
- redis (exception: uses REDIS_PORT)
- qdrant (exception: native config)
- conport (migrate to contract)
- dopecon-bridge (migrate to contract)
- task-orchestrator (migrate to contract)

### Phase 3: Full Ecosystem (Future)
- ⏳ Migrate remaining 42 services
- ⏳ Enable metrics for all services
- ⏳ Standardize observability

## References

- **Service Registry**: `services/registry.yaml`
- **Drift Scanner**: `tools/env_drift_scan.py`
- **Architecture Tests**: `tests/arch/test_service_env_contract.py`
- **Smoke Compose**: `docker-compose.smoke.yml`
- **Env Matrix**: `reports/g33/env_support_matrix.md`

---

**Maintainer**: Dopemux Platform Team
**Last Review**: 2026-02-01
**Next Review**: 2026-03-01 (30 days)
