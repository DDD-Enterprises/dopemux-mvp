# REPO_IDENTITY.md — Serena v2

## Analyzed Ref
```
fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2
```
Branch: `codex/main-drain-20260306`

## Repository
- **Host repository**: `/Users/hue/code/dopemux-mvp` (local)
- **Target path**: `services/serena/`
- **Remote**: Local-only analysis (no remote queried)

## Package Identity
- **Module `__version__`**: `"2.0.0"` (`services/serena/__init__.py:5`)
- **Egg-info package name**: `dopemux-serena` version `0.1.0` (`services/serena/src/dopemux_serena.egg-info/PKG-INFO`)
- **Module description**: `"Serena — ADHD-Optimized Code Intelligence System"` (`services/serena/__init__.py:2`)
- **MCP server name**: `"serena-v2"` (`mcp_server.py:395` → `Server("serena-v2")`)

## Version Discrepancy
| Source | Version |
|--------|---------|
| `__init__.py` `__version__` | `2.0.0` |
| `PKG-INFO` metadata | `0.1.0` |
| `mcp_server.py` Server name | `serena-v2` |
| `mcp_server.py` docstring | `"Phase 2 + Enhanced Features"` |
| Docker info_server.py | `"Serena v2"` |

**Authoritative version**: `2.0.0` (from `__init__.py`)

## Language & Runtime
- **Primary language**: Python 3.11+
- **Runtime**: asyncio event loop
- **MCP SDK**: `mcp>=0.9.0` (from PKG-INFO requires)
- **Key dependencies**: asyncpg, redis.asyncio, pydantic, tree-sitter, mcp, fastapi, uvicorn

## Source Statistics
| Category | Files | Lines (approx) |
|----------|-------|----------------|
| Root modules (`services/serena/*.py`) | 43 | ~27,395 |
| Intelligence engine (`intelligence/*.py`) | 27 | ~27,243 |
| Tests | 12 | ~4,778 |
| Build/Runtime artifacts | 7 | — |
| Docker/Compose/Config references | 10 | — |
| Documentation (external) | 23 | — |
| **Total** | **122** | **~54,638+** |

## Service Registry Entry
From `services/registry.yaml`:
- **Service name**: `serena`
- **Port**: `3006`
- **Health endpoint**: `/health`
- **Category**: `mcp`
- **Docker compose service**: `serena`

## Build & Entry Points
| Entry Point | File | Transport | Port |
|-------------|------|-----------|------|
| `main()` → `stdio_server()` | `mcp_server.py:5326` | stdio | N/A |
| `if __name__ == "__main__"` | `mcp_server.py:5371` | stdio | N/A |
| FastAPI `app` | `http_server.py:54` | HTTP | 8003 |
| Docker wrapper (mcp-proxy) | `docker/mcp-servers-source/serena/wrapper.py` | SSE | 3006 |
| Docker info server | `docker/mcp-servers-source/serena/info_server.py` | HTTP | 4006 |

## Dual Codebase Warning
Two distinct "Serena" implementations exist:
1. **`services/serena/`** — 54K+ lines custom dopemux code, 33 MCP tools, intelligence engine
2. **`docker/mcp-servers-source/serena/`** — Thin wrapper around `pip install git+https://github.com/oraios/serena.git` (upstream OSS)

The `compose.yml` builds from (2), NOT from (1). This is a known architectural divergence.
