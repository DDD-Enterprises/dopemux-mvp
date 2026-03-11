# EXECUTIVE SUMMARY — dope-memory

## What It Is

Dope-Memory is a **temporal chronicle and working-context manager** for the Dopemux developer workflow platform. It captures, curates, and retrieves chronological work log entries across coding sessions, providing ADHD-optimized context restoration via deterministic promotion, search, and reflection.

## Key Characteristics

- **10 MCP tool endpoints** exposed over HTTP/FastAPI on port 3020
- **SQLite canonical ledger** as single source of truth (per ADR-213), with optional PostgreSQL mirror
- **Deterministic promotion pipeline**: raw events → redaction → allowlist check → curated entry (no LLM)
- **Supersession chains** for immutable corrections (max depth 10, linear, fork-prevented)
- **ADHD Top-3 boundary** on all search/recap responses with cursor-based pagination
- **Real-time ingestion** via Redis Streams (`activity.events.v1`) through EventBus consumer
- **Phase 2 reflection/trajectory** system: deterministic reflection cards + trajectory-based search boost

## Architecture Position

One of three Memory Trinity services in Dopemux:

| Service | Role | Storage |
|---------|------|---------|
| **DopeContext** | Semantic archival retrieval | Qdrant (vectors) |
| **DopeQuery (ConPort)** | Structured truth and decisions | PostgreSQL + AGE |
| **Dope-Memory** (this) | Temporal chronicle and working-context | SQLite + Postgres mirror |

## Critical Findings

### Healthy
- ✅ 10 HTTP tool endpoints fully implemented with Pydantic validation
- ✅ Comprehensive test suite (25+ test files, 60+ test functions)
- ✅ Deterministic entry IDs (SHA-256 of provenance fingerprint)
- ✅ Mandatory provenance chain on all entries (sentinel ban for runtime)
- ✅ Supersession semantics fully implemented with chain depth limits and fork prevention

### Drift / Gaps
- ⚠️ **SSE transport not implemented**: `.claude.json` configures SSE at `/mcp` but no such endpoint exists in server code
- ⚠️ **Two divergent DopeMemoryMCPServer classes**: `dope_memory_main.py` (10 tools, authoritative) vs `mcp/server.py` (7 tools, shadowed)
- ⚠️ **Root endpoint lists 7 tools** but 10 routes are registered (missing Phase 2 tools)
- ⚠️ **Stdio adapter targets wrong port**: `mcp_stdio_adapter.py` proxies to port 8096 (legacy WMA), not 3020
- ⚠️ **Two services share one directory**: `services/working-memory-assistant/` hosts both dope-memory (port 3020) and legacy WMA (port 8096) with separate Dockerfiles

### Integration Readiness
- **HTTP REST**: Production-ready, all 10 tools callable via `POST /tools/{tool_name}`
- **MCP Protocol**: Not natively implemented; requires external MCP proxy for JSON-RPC compliance
- **Redis Streams**: Production-ready consumer with configurable streams and consumer groups
- **PostgreSQL Mirror**: Opt-in, one-way sync (SQLite → Postgres), gated by feature flag

## Tool Inventory (Authoritative — dope_memory_main.py)

| # | Tool Name | Category | Pagination |
|---|-----------|----------|------------|
| 1 | `memory_search` | Query | cursor + top_k |
| 2 | `memory_store` | Write | — |
| 3 | `memory_recap` | Query | top_k |
| 4 | `memory_mark_issue` | Write | — |
| 5 | `memory_link_resolution` | Write | — |
| 6 | `memory_replay_session` | Query | cursor + top_k |
| 7 | `memory_correct` | Write | — |
| 8 | `memory_generate_reflection` | Write/Query | — |
| 9 | `memory_reflections` | Query | limit |
| 10 | `memory_trajectory` | Query | — |
