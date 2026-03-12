# REPO_IDENTITY — dope-memory

## Repository

| Field | Value |
|-------|-------|
| Repo URL | `https://github.com/DDD-Enterprises/dopemux-mvp.git` |
| Repo Name | `dopemux-mvp` |
| Target Service | `dope-memory` |
| Analyzed Ref | `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2` |
| Analyzed Branch | `codex/main-drain-20260306` |
| Commit Timestamp | `2026-03-06 12:22:43 -0800` |
| Commit Author | `DDD-Enterprises` |
| Commit Message | `chore(ci): checkpoint pr merge-readiness fixes` |
| Default Branch | `codex/main-drain-20260306` (at HEAD) |
| Latest Release Tags | `v9.0.3`, `v9.0.2`, `v9.0.1`, `v9.0.0`, `v8.0.2` |

## Primary Languages

| Language | Scope |
|----------|-------|
| Python 3.11 | Service implementation, tests |
| SQL (SQLite) | Schema DDL, migrations |
| SQL (PostgreSQL) | Mirror schema |

## Runtimes

| Runtime | Version | Evidence |
|---------|---------|----------|
| Python | 3.11 | `Dockerfile.dope-memory` `FROM python:3.11-slim` |
| SQLite | system | `Dockerfile.dope-memory` `apt-get install sqlite3` |

## Build System

| Component | Tool | Evidence |
|-----------|------|----------|
| Package Manager | pip | `requirements.txt` |
| Container Build | Docker | `Dockerfile.dope-memory` |
| Compose | docker-compose | `compose.yml`, `docker-compose.smoke.yml` |

## Packaging

| Artifact | Evidence |
|----------|----------|
| Docker image `dope-memory` | `Dockerfile.dope-memory` in `services/working-memory-assistant/` |
| No PyPI package | Service is deployed as Docker container only |

## Key Dependencies (requirements.txt)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.104.1 | HTTP framework |
| `uvicorn[standard]` | 0.24.0 | ASGI server |
| `pydantic` | 2.5.0 | Request/response validation |
| `redis` | 5.0.1 | EventBus consumer (async) |
| `psycopg2-binary` | 2.9.9 | PostgreSQL mirror sync |
| `asyncpg` | 0.29.0 | Async PostgreSQL driver |
| `aiohttp` | 3.9.1 | HTTP client (DopeContext index) |
| `structlog` | 23.2.0 | Structured logging |
| `prometheus-client` | 0.19.0 | Metrics |
| `lz4` | 4.3.3 | Compression (WMA legacy) |
| `zstandard` | 0.22.0 | Compression (WMA legacy) |
| `numpy` | 1.24.3 | Predictive context (WMA legacy) |

Note: Several dependencies (`lz4`, `zstandard`, `numpy`, `alembic`, `sqlalchemy`) are WMA-era legacy and not used by the `dope_memory_main.py` entrypoint. They remain in `requirements.txt` because the same directory hosts both services.
