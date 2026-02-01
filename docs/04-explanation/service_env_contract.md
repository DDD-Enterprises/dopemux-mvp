---
id: service_env_contract
title: Service Environment Variable Contract
type: explanation
date: '2026-02-01'
author: '@hu3mann'
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---

Canonical environment variable contract for all smoke-enabled Dopemux services. Defines required vars (HOST, PORT, LOG_LEVEL) with defaults, optional vars (BASE_URL), implementation patterns, and enforcement via drift scanner and architecture tests.

# Service Environment Variable Contract

**Version**: 1.0
**Last Updated**: 2026-02-01
**Status**: CANONICAL

## Purpose

This document defines the **mandatory environment variable contract** for all smoke-enabled Dopemux services. The contract ensures:

1. **Consistent startup behavior** across services
2. **No "build passes, runtime dies" failures** due to env drift
3. **Clear defaults** that work in development and production
4. **Minimal configuration burden** for service implementers

## Scope

This contract applies to:
- All services with `enabled_in_smoke: true` in `services/registry.yaml`
- Python-based services only (infrastructure services use native configuration)
- Service startup and configuration modules only

## Required Environment Variables

### HOST

**Purpose**: Bind address for the service's HTTP server
**Type**: String
**Default**: `0.0.0.0`
**Example**: `HOST=0.0.0.0` or `HOST=127.0.0.1`

**Rationale**: `0.0.0.0` allows the service to accept connections from any network interface, which is required for Docker container networking.

**Implementation**:
```python
HOST = os.getenv("HOST", "0.0.0.0")
```

### PORT

**Purpose**: TCP port for the service's HTTP server
**Type**: Integer
**Default**: Must match `container_port` from `services/registry.yaml`
**Example**: `PORT=3004` (for conport)

**Rationale**: Port must align with registry to prevent "service running on wrong port" failures.

**Implementation**:
```python
# For service with registry container_port: 3004
PORT = int(os.getenv("PORT", "3004"))
```

**Special cases**:
- Services using `PORT_BASE` pattern (e.g., dopecon-bridge at `PORT_BASE + 16`) should continue using that pattern but also support explicit `PORT` override:
  ```python
  PORT_BASE = int(os.getenv("PORT_BASE", "3000"))
  DEFAULT_PORT = PORT_BASE + 16
  PORT = int(os.getenv("PORT", str(DEFAULT_PORT)))
  ```

### LOG_LEVEL

**Purpose**: Logging verbosity level
**Type**: String (enum)
**Default**: `info`
**Valid values**: `debug`, `info`, `warning`, `error`, `critical`
**Example**: `LOG_LEVEL=debug`

**Rationale**: Consistent logging configuration across all services for debugging and production observability.

**Implementation**:
```python
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
```

## Optional Environment Variables

### BASE_URL

**Purpose**: External URL for the service (used by bridge/client services)
**Type**: String (URL)
**Default**: `http://localhost:<port>` (if service is a client/bridge), otherwise not required
**Example**: `BASE_URL=http://localhost:3016` (or `http://dopecon-bridge:3016` in Docker network)

**When required**: Only for services that act as HTTP clients to other services (e.g., dopecon-bridge calling conport).

**Implementation**:
```python
# For bridge/client services only
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{PORT}")
```

## Implementation Requirements

### 1. Missing Environment Variables Must Not Crash

Services **MUST NOT** use `os.environ["VAR"]` without a fallback. Always provide a default:

❌ **BAD**:
```python
PORT = int(os.environ["PORT"])  # Crashes if PORT not set
```

✅ **GOOD**:
```python
PORT = int(os.getenv("PORT", "3004"))  # Uses default if PORT not set
```

### 2. Invalid Environment Variables Should Fail Fast

If a provided value is invalid, fail with a clear error message at startup:

```python
try:
    PORT = int(os.getenv("PORT", "3004"))
    if not (1024 <= PORT <= 65535):
        raise ValueError(f"PORT must be between 1024 and 65535, got {PORT}")
except ValueError as e:
    logger.error(f"Invalid PORT configuration: {e}")
    sys.exit(1)
```

### 3. Single Source of Configuration

Each service should have **ONE** centralized location for env parsing:
- Preferred: `config.py` or `settings.py`
- Acceptable: Top of `main.py` or `app.py`

**Do not**:
- Scatter `os.getenv()` calls throughout the codebase
- Parse the same env var in multiple places
- Use different defaults in different modules

### 4. Settings Validation Pattern

Recommended pattern using Pydantic (if available) or dataclass:

```python
from pydantic import BaseSettings, Field

class ServiceSettings(BaseSettings):
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=3004, env="PORT")
    LOG_LEVEL: str = Field(default="info", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = ServiceSettings()
```

Or with plain Python:

```python
import os
import sys

class ServiceConfig:
    def __init__(self):
        self.HOST = os.getenv("HOST", "0.0.0.0")

        try:
            self.PORT = int(os.getenv("PORT", "3004"))
        except ValueError as e:
            print(f"ERROR: Invalid PORT value: {e}", file=sys.stderr)
            sys.exit(1)

        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()

    def validate(self):
        if self.PORT < 1024 or self.PORT > 65535:
            raise ValueError(f"PORT must be 1024-65535, got {self.PORT}")

        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.LOG_LEVEL not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}, got {self.LOG_LEVEL}")

config = ServiceConfig()
config.validate()
```

## Registry Exceptions

If a service legitimately does not need one of the required variables, document it in `services/registry.yaml`:

```yaml
- name: special-service
  port: 9000
  container_port: 9000
  enabled_in_smoke: true
  env_contract_exceptions:
    - HOST  # Service uses Unix socket instead of TCP
  env_contract_exception_reason: "Uses Unix domain socket for IPC, not TCP/IP"
```

## Testing Requirements

All smoke-enabled services must pass the environment contract test:

```bash
pytest tests/arch/test_service_env_contract.py
```

This test verifies:
1. Service supports required env vars (HOST, PORT, LOG_LEVEL)
2. Service has single config source (not scattered os.getenv)
3. Service does not use risky patterns (os.environ["VAR"], sys.path.insert)

## Migration Guide

For existing services that don't comply:

1. **Locate current env parsing**: Find where `PORT`, `HOST`, etc. are currently read
2. **Create/update config module**: Centralize env parsing in `config.py` or `settings.py`
3. **Add defaults**: Ensure all required vars have defaults matching this contract
4. **Add validation**: Fail fast on invalid values with clear error messages
5. **Update entry point**: Use config object instead of inline `os.getenv()`
6. **Test**: Run `pytest tests/arch/test_service_env_contract.py`

## Enforcement

This contract is enforced by:
1. **Static analysis**: `tools/env_drift_scan.py` scans for missing support
2. **Architecture tests**: `tests/arch/test_service_env_contract.py` fails on violations
3. **Smoke stack validation**: Services must boot successfully with only defaults

## References

- Service Registry: `services/registry.yaml`
- Drift Scanner: `tools/env_drift_scan.py`
- Contract Tests: `tests/arch/test_service_env_contract.py`
- Matrix Report: `reports/g33/env_support_matrix.md`
