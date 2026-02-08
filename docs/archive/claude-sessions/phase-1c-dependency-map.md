---
id: phase-1c-dependency-map
title: Phase 1C Dependency Map
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Phase 1C Dependency Map (explanation) for dopemux documentation and developer
  workflows.
---
# Phase 1C: Dependency & Config Mapping
**Date**: 2025-10-16
**Duration**: 30 minutes
**Method**: Config file analysis + semantic search
**Status**: ✅ Complete

---

## Infrastructure Dependencies

### Database Layer

**PostgreSQL Instances**:
1. **Primary** (port 5432)
   - Used by: Multi-database setup
   - Purpose: Primary data storage

2. **AGE Extension** (port 5455)
   - Database: `dopemux_knowledge_graph`
   - User: `dopemux_age`
   - Used by: ConPort KG (graph database)
   - Extension: Apache AGE (graph queries)

**MySQL**:
- **Leantime** (port 3306)
- User: `leantime`
- Database: `leantime`
- Purpose: PM plane (Leantime project management)

**Redis Instances**:
1. **Primary** (port 6379)
   - Event bus (Redis Streams)
   - General caching
   - Password: Optional (configurable)

2. **Leantime** (port 6380)
   - Dedicated Redis for Leantime
   - Isolated from event bus

**Qdrant** (port 6333):
- Used by: Dope-Context
- Collections: code_{hash}, docs_{hash}
- Purpose: Vector search

**Milvus** (port 19530):
- Used by: Claude-Context (legacy?)
- Includes: etcd + minio
- Web UI: port 19121
- Status: Unclear if active

---

## Service Port Allocation

**Base**: PORT_BASE = 3000 (configurable)

| Service | Offset | Port | Type | Status |
|---------|--------|------|------|--------|
| (Reserved) | +1 | 3001 | - | - |
| PAL apilookup | +2 | 3003 | MCP | Active |
| Zen | +3 | 3003 | MCP | Active |
| ConPort | +4 | 3004 | MCP | Active |
| Task Master | +5 | 3005 | MCP | ? |
| Serena | +6 | 3006 | MCP | Active |
| Claude Context | +7 | 3007 | MCP | Legacy? |
| GPT-R MCP | +9 | 3009 | MCP | Active |
| MorphLLM | +11 | 3011 | MCP | ? |
| Desktop Commander | +12 | 3012 | MCP | ? |
| Leantime Bridge | +15 | 3015 | MCP | ? |
| **DopeconBridge** | **+16** | **3016** | **API** | **Implemented** |

**Additional Services**:
- Leantime: 8080 (PM plane web UI)
- Redis Commander: 8081 (Redis management)
- Minio Console: 9001 (object storage)
- ADHD Engine: 8090 (FastAPI)
- GPT-Researcher: 8000 (FastAPI)

---

## Python Dependencies (from requirements.txt)

### Core Web Framework
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `pydantic>=2.0.0` - Data validation

### Async & HTTP
- `asyncio>=3.4.3` - Async support
- `aiohttp>=3.12.14` - **Security**: CVE fixes (CVE-2025-53643, directory traversal, DoS)

### AI & Embeddings
- `voyageai>=0.2.0` - Vector embeddings (voyage-code-3, voyage-context-3)
- `openai>=1.0.0` - GPT models for context generation
- `pymilvus>=2.3.0` - Milvus vector DB client
- `chromadb>=0.4.0` - Alternative vector DB

### ML & Data Science
- `numpy>=1.24.0` - Numerical computing
- `scipy>=1.10.0` - Scientific computing
- `scikit-learn>=1.3.0` - ML algorithms

### Document Processing
- `pandoc>=2.3` - Document conversion
- `chardet>=5.0.0` - Character encoding detection

### Configuration
- `python-dotenv>=1.0.0` - Environment variable loading
- `typer>=0.9.0` - CLI framework

### UI/Display
- `rich>=13.0.0` - Terminal UI formatting

---

## External API Dependencies

**VoyageAI API**:
- Models: voyage-code-3 (code), voyage-context-3 (docs), voyage-rerank-2.5
- Rate limits: 2000 RPM
- Used by: Dope-Context (embeddings + reranking)
- Cost: ~$0.12 per 1M tokens

**Anthropic API**:
- Model: claude-3-5-haiku-20241022 (context generation)
- Used by: Dope-Context (optional), GPT-Researcher
- Rate limits: 50 RPM, 50K tokens/min

**OpenAI API**:
- Models: gpt-5-pro, gpt-5-codex, gpt-5, gpt-5-mini, etc.
- Used by: Zen MCP (27 models), Task-Orchestrator
- Rate limits: Varies by model

---

## Service-to-Service Dependencies

### Direct Database Access (❌ Violations)

**ADHD Engine → ConPort SQLite**:
- **Pattern**: Direct SQLite writes
- **Location**: `conport_client.py:296`
- **Violation**: Bypasses DopeconBridge authority
- **Impact**: Two services writing same database
- **Severity**: MEDIUM (documented, Week 7 fix)

### HTTP API Dependencies

**ConPort KG UI → DopeconBridge**:
- **Client**: `kgClient.ts`
- **Methods**: `getRecentDecisions(3)`, `getNeighborhood()`, `getFullContext()`
- **Port**: 3016 (DopeconBridge)
- **Status**: ✅ Proper integration

### Event Bus Dependencies (Redis Streams)

**Producers**:
- Task-Orchestrator (orchestration events)
- Serena (navigation events)
- (ADHD Engine planned)

**Consumers**:
- DopeconBridge (coordinator)
- ConPort Orchestrator (automation triggers)

**Status**: Infrastructure exists, partial adoption

---

## Configuration Patterns

### Environment Variables Found (from docker-compose)

**Database Config**:
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `AGE_HOST`, `AGE_PORT`, `AGE_PASSWORD`
- `REDIS_URL`, `REDIS_PASSWORD`

**Port Config**:
- `PORT_BASE` (default: 3000)
- Service-specific offsets (+1 to +18)

**Feature Flags**:
- `KG_DIRECT_CONNECTION` (DopeconBridge)
- `CONFLICT_ALERTS` (Task-Orchestrator)
- `DEPENDENCY_VIZ` (Task-Orchestrator)
- `SMART_BATCHING` (Task-Orchestrator)

**Instance Config**:
- `DOPEMUX_INSTANCE` (multi-instance support)
- `WORKSPACE_ID` (workspace isolation)

---

## Docker Compose Files Found

1. `docker/conport-kg/docker-compose.yml` - ConPort production setup
2. `docker/memory-stack/docker-compose.yml` - Memory infrastructure
3. `docker/leantime/docker-compose.yml` - PM plane
4. `docker/docker-compose.event-bus.yml` - Redis event bus
5. `docker/mcp-servers/zen/docker-compose.yml` - Zen MCP

**Architecture**: Service-per-container with shared network

---

## Network Architecture

**Docker Networks**:
- `conport-kg-network` - ConPort isolation
- `mcp-network` - MCP servers (likely)
- Default bridge for other services

**Service Discovery**: Via container names (e.g., `postgres-age`, `conport-kg-redis`)

---

## Security Findings

### Dependency Vulnerabilities

**aiohttp>=3.12.14** - ✅ PATCHED:
- CVE-2025-53643 (directory traversal)
- CVE-2024-52304 (DoS)
- Security updates applied

### Configuration Risks

⚠️ **Hardcoded Defaults**:
- `AGE_PASSWORD:-dopemux_age_dev_password` (dev password in compose file)
- `allow_origins=["*"]` (CORS - ADHD Engine main.py:96)

🔴 **Production Concerns**:
- CORS wildcard in production
- Default passwords in docker-compose
- No secrets management visible

---

## Multi-Instance Support

**Port Strategy**: Multiples of 30
- Instance 1: BASE=3000
- Instance 2: BASE=3030
- Instance 3: BASE=3060

**Shared Resources** (efficiency):
- MCP shared data volumes
- Semantic code embeddings
- Search result cache
- Milvus data

**Isolation**:
- Separate port ranges
- Instance ID environment variable
- Workspace ID separation

---

## Phase 1C Conclusion

### Dependency Summary

**Databases**: 5 instances (PostgreSQL x2, MySQL, Redis x2)
**Vector DBs**: 2 (Qdrant, Milvus)
**External APIs**: 3 (VoyageAI, Anthropic, OpenAI)
**Docker Services**: 12+ containers across multiple compose files

### Key Findings

✅ **Well-Structured**:
- Clear port allocation strategy
- Multi-instance support
- Health checks configured
- Network isolation

⚠️ **Security Concerns**:
- Hardcoded default passwords
- CORS wildcards
- No secrets management

❌ **Architecture Violations**:
- Direct database access (ADHD Engine)
- DopeconBridge bypassed

---

**Phase 1C Complete** ✅
**Time**: ~30 minutes
**Next**: Phase 1D - Documentation Inventory (10 min, mostly done!)
