# DRIFT_REPORT.md — dope-context

**Analyzed ref:** `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

---

## Drift Methodology

Each discrepancy is classified by:
- **Source:** Where the claim originates (docs, config, tests, code)
- **Severity:** High (functional mismatch), Medium (operational risk), Low (cosmetic/aspirational)
- **Type:** `docs_say_code_doesnt`, `code_does_docs_dont`, `config_aspirational`, `wrapper_mismatch`, `test_gap`

---

## Discrepancy Table

| # | Description | Docs Say | Code Does | Severity | Type | Evidence |
|---|------------|----------|-----------|----------|------|----------|
| D-01 | **API index not implemented** | `multi_index_config.yaml` defines an `api` index type (OpenAPI/Swagger/GraphQL) | No pipeline, no tools, no handler for API index type | Medium | config_aspirational | `config/multi_index_config.yaml` vs all `server.py`, `pipeline/` |
| D-02 | **Chat index not implemented** | `multi_index_config.yaml` defines a `chat` index type (conversation transcripts) | No pipeline, no tools, no handler for chat index type | Medium | config_aspirational | `config/multi_index_config.yaml` vs all `server.py`, `pipeline/` |
| D-03 | **Export formats not implemented** | README.md:556-558 claims JSON, Markdown, and CSV export formats | No CSV export, no Markdown export tools exist in MCP surface | Low | docs_say_code_doesnt | README.md vs server.py |
| D-04 | **Zen integration not implemented** | README.md describes Zen integration | No code reference to "Zen" in any source file | Low | docs_say_code_doesnt | README.md vs `grep -r "zen\|Zen" src/` |
| D-05 | **Wrapper script path mismatch** | `dope-context-wrapper.sh` calls `python /app/server.py "$@"` | Docker CMD is `python -m src.mcp.server`. No `/app/server.py` exists in Docker image | Medium | wrapper_mismatch | `scripts/mcp-wrappers/dope-context-wrapper.sh:62` vs `Dockerfile:47` |
| D-06 | **Redis caching not implemented** | `requirements.txt` includes `redis>=5.0.0`, `aioredis>=2.0.1` | Server.py does not use Redis for any caching. Code comments reference "Phase 3" caching | Low | config_aspirational | `requirements.txt` vs `server.py` |
| D-07 | **ConPort integration test gap** | `CONPORT_INTEGRATION_AVAILABLE` flag exists with conditional import | No test exercises the ConPort integration path (True case) | Medium | test_gap | `server.py:69-73` vs `tests/test_mcp_server.py` |
| D-08 | **Nested duplicate files** | N/A | `services/dope-context/services/dope-context/Dockerfile` and `.dockerignore` exist as accidental nested copies | Low | code_does_docs_dont | Filesystem |
| D-09 | **ADHD dynamic top_k not tested** | `get_dynamic_top_k` implements attention-aware result limits | No test exercises the ADHD Engine path with actual feature flag checks | Medium | test_gap | `server.py:313-339` vs `tests/` |
| D-10 | **Decision search not tested end-to-end** | `_search_decisions_impl` calls dopecon-bridge HTTP API | No test exercises the HTTP call to dopecon-bridge | Medium | test_gap | `server.py:1904-1959` vs `tests/` |
| D-11 | **`/info` endpoint protocol field** | `/info` returns `"protocol": "stdio" if transport == "stdio" else "sse"` | When transport is `"http"` or `"streamable-http"`, protocol is still reported as `"sse"` | Low | code_does_docs_dont | `server.py:167` |
| D-12 | **Code graph enrichment import path** | `from enrichment.code_graph_enricher import get_code_graph_enricher` | Relative import uses bare `enrichment.` which would fail unless PYTHONPATH includes `src/` parent | Low | code_does_docs_dont | `server.py:1290` |
| D-13 | **Backup test file** | N/A | `tests/test_mcp_server.py.bak` exists as inactive backup | Low | code_does_docs_dont | Filesystem |

---

## Summary

| Severity | Count |
|----------|-------|
| High | 0 |
| Medium | 6 |
| Low | 7 |
| **Total** | **13** |

### Critical Observations

1. **No high-severity drift.** The core MCP tools (18 tools + 4 routes) are all implemented and functional.
2. **The aspirational config drift (D-01, D-02)** is the most significant: `multi_index_config.yaml` describes a 4-index architecture but only 2 of 4 indexes are implemented.
3. **The wrapper script mismatch (D-05)** would cause runtime failures if the wrapper is used without correction.
4. **Test gaps (D-07, D-09, D-10)** affect ConPort integration, ADHD Engine, and decision search — all conditional/optional features.

---

## Recommendations

1. **D-05 (wrapper path):** Fix `dope-context-wrapper.sh` to use `python -m src.mcp.server` instead of `python /app/server.py`.
2. **D-01, D-02:** Either implement api/chat indexes or remove from `multi_index_config.yaml` with a note that they are deferred.
3. **D-03:** Remove export format claims from README or implement them.
4. **D-07, D-09, D-10:** Add integration-level tests for ConPort, ADHD Engine, and decision search paths.
5. **D-08:** Remove nested duplicate `services/dope-context/services/dope-context/` directory.
