# REPO_IDENTITY.md — dope-context

**Generated:** Phase 2 extraction
**Analyzed ref:** `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**Branch:** `codex/main-drain-20260306`

---

## Identity

| Field | Value | Evidence |
|-------|-------|----------|
| **Repository** | `dopemux-mvp` | Git root |
| **Service path** | `services/dope-context/` | Filesystem |
| **Package name** | `dope-context-mcp` | `src/mcp/setup.py:6` |
| **FastMCP server name** | `"dope-context"` | `server.py:90` |
| **Version** | `1.0.0` | `server.py:163`, `src/mcp/setup.py:6` |
| **Python requirement** | `>=3.11` | `src/mcp/setup.py:9`, `Dockerfile:1` |
| **Default port** | `3010` | `server.py:119`, `Dockerfile ENV`, `compose.yml:337` |
| **Docker image base** | `python:3.11-slim` | `Dockerfile:1`, `Dockerfile.fixed:1` |
| **Container name** | `mcp-dope-context` | `compose.yml:317` |
| **Primary entrypoint** | `python -m src.mcp.server` | `server.py:3029-3043`, `Dockerfile:47` |
| **PYTHONPATH** | `/app/src` | `Dockerfile:33`, `Dockerfile.fixed:34` |
| **License** | UNKNOWN | No LICENSE in service directory |

## Description

Semantic code and documentation search MCP server with ADHD-optimized result delivery. Provides hybrid dense+sparse vector search with reranking, autonomous file monitoring, incremental indexing, and cross-plane decision integration via Trinity architecture boundaries.

## Role in Dopemux

dope-context is the **search plane authority** in the Three-Plane Trinity Architecture:
- **Search plane** (dope-context): code/docs retrieval, fusion, rerank, search provenance
- **Memory plane** (ConPort/dopecon-bridge): decision lifecycle, decision truth records
- **Cognitive plane** (ADHD engine/Serena): attention-aware result tuning

dope-context reads decisions from the memory plane (read-only) but never writes to it.

## Dependencies

### External Services
| Service | Purpose | Connection |
|---------|---------|------------|
| Qdrant | Vector storage | `QDRANT_URL` (default: `localhost`), `QDRANT_PORT` (default: `6333`) |
| Voyage AI | Embeddings + reranking | `VOYAGE_API_KEY` or `VOYAGEAI_API_KEY` |
| OpenAI | Context generation | `OPENAI_API_KEY` (optional) |
| dopecon-bridge | Decision retrieval | `DOPECON_BRIDGE_URL` (default: `http://localhost:3016`) |
| ADHD Engine | Dynamic top_k | Feature-flagged, optional |
| Redis | Event bus (integration) | `redis://localhost:6379` (conditional) |

### Compose Dependencies
- `mcp-qdrant` (hard dependency via `depends_on`)

## File Count

| Category | Count |
|----------|-------|
| Source files (src/) | ~30 |
| Test files | 5 active + 1 backup |
| Config files | 1 (multi_index_config.yaml) |
| Build files | 3 (Dockerfile, Dockerfile.fixed, requirements.txt) |
| Contract schemas | 2 (in contracts/dope-context/) |
