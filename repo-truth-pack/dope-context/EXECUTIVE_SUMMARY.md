# EXECUTIVE_SUMMARY.md — dope-context

**Analyzed ref:** `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**Branch:** `codex/main-drain-20260306`
**Phase:** 2 (Full Extraction)

---

## Service Identity

**dope-context** is a semantic code and documentation search MCP server built on FastMCP, providing hybrid retrieval (dense + sparse + rerank) with ADHD-optimized result delivery and autonomous zero-touch indexing.

| Property | Value |
|----------|-------|
| Package name | `dope-context-mcp` |
| Version | `1.0.0` |
| Port | `3010` |
| Python | `>=3.11` |
| Authoritative source | `services/dope-context/src/mcp/server.py` (3043 lines) |

---

## Callable Surface

### MCP Tools: 18
| Category | Tools |
|----------|-------|
| **Indexing** (3) | `index_workspace`, `index_docs`, `clear_index` |
| **Search** (3) | `search_code`, `docs_search`, `search_all` |
| **Sync** (2) | `sync_workspace`, `sync_docs` |
| **Autonomous** (5) | `start_autonomous_indexing`, `stop_autonomous_indexing`, `get_autonomous_status`, `start_autonomous_docs_indexing`, `stop_autonomous_docs_indexing` |
| **Metrics** (2) | `get_search_metrics`, `clear_search_metrics` |
| **Status** (1) | `get_index_status` |
| **Analysis** (1) | `get_chunk_complexity` |
| **Config** (1) | `configure_decision_auto_indexing` |

### Custom HTTP Routes: 4
`/health` (GET), `/info` (GET), `/autoindex/bootstrap` (POST), `/autoindex/status` (GET)

---

## Architecture Highlights

### Three-Plane Trinity Architecture
- **Search Plane** (dope-context): Code/docs retrieval, fusion, reranking — full authority
- **Memory Plane** (ConPort): Decisions — read-only access from dope-context
- **Cognitive Plane** (ADHD Engine): Attention state — read-only access from dope-context

### Search Pipeline
```
Query → Voyage Embedding (3 vectors) → Hybrid Search (Dense + BM25 RRF) → Voyage Reranking → Token Budget Truncation → Results
```

### Persistence
- **Primary:** Qdrant (vectors, collections named `code_{hash}`, `docs_{hash}`)
- **Secondary:** `~/.dope-context/snapshots/` (SHA256 snapshots, BM25 cache, config, markers)
- **No SQLite, no Redis for storage** (Redis used only for ADHD Engine feature flags)

### Transports
stdio (default), HTTP (Docker default, port 3010), SSE, streamable-http

---

## Dependencies

| Service | Type | Required |
|---------|------|----------|
| Qdrant | Vector store | **Hard** |
| Voyage AI | Embeddings + reranking | **Hard** |
| OpenAI | Context generation | Soft (optional) |
| dopecon-bridge | Decision enrichment | Soft (config-gated) |
| ADHD Engine | Dynamic top_k | Soft (feature-flagged) |
| Serena | Code graph enrichment | Soft (parameter-gated) |

---

## Drift Summary

| Severity | Count | Key Items |
|----------|-------|-----------|
| High | 0 | — |
| Medium | 6 | API/chat indexes unimplemented, wrapper path mismatch, test gaps for ConPort/ADHD/decisions |
| Low | 7 | Export formats claimed but missing, Zen integration not in code, nested duplicate files |

**No high-severity drift.** Core tool surface is fully implemented and functional.

---

## Phase 2 Deliverables

| Artifact | Status |
|----------|--------|
| `REPO_IDENTITY.md` | ✅ Generated |
| `TOOL_MANIFEST.json` | ✅ Generated (18 tools + 4 routes) |
| `CONTRACT_SCHEMAS/*.json` | ✅ Generated (17 schema files) |
| `ARCHITECTURE_AND_INTENDED_USES.md` | ✅ Generated |
| `WORKFLOW_AND_GATES.md` | ✅ Generated (11 workflows) |
| `DATA_MODEL.md` | ✅ Generated |
| `TRANSPORT_AND_RUNBOOK.md` | ✅ Generated (4 transports) |
| `DRIFT_REPORT.md` | ✅ Generated (13 discrepancies) |
| `INTEGRATION_NOTES.md` | ✅ Generated (7 integration points) |
| `EXECUTIVE_SUMMARY.md` | ✅ Generated |
| `COMMAND_LOG.md` | ✅ Appended |
| `INSPECTED_FILES.txt` | ✅ Appended |
| `SEARCH_PATTERNS.txt` | ✅ Appended |

---

## Key Observations

1. **Well-structured service** with clear module boundaries and lazy initialization
2. **Comprehensive multi-workspace support** across all tools
3. **Explicit authority boundaries** (Trinity constants in code)
4. **Graceful degradation** on all soft dependencies
5. **Token budget enforcement** prevents MCP response overflow
6. **Aspirational config** (4 indexes) outpaces implementation (2 indexes)
7. **Test coverage** covers core tools but not integration paths
