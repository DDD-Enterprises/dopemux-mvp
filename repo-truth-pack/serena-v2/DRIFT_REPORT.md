# DRIFT_REPORT.md — Serena v2

Analyzed ref: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

## 1. Tool Count Drift

| Source | Claimed Count | Actual (code) | Delta |
|--------|--------------|----------------|-------|
| `mcp_server.py` docstring (line 10) | "21+" | 33 | +12 |
| `main()` log output (line 5330) | 24 | 33 | +9 |
| `get_workspace_status_tool` response (line 1608) | 20 (total_available) | 33 | +13 |
| Phase 1 discovery notes | 32 | 33 | +1 |
| `list_tools()` array | 33 | 33 | 0 (authoritative) |
| `call_tool()` dispatch | 33 | 33 | 0 (authoritative) |

**Root cause**: Docstring and log output were not updated when new tools were added. The `get_workspace_status_tool` returns hardcoded counts that lag behind actual registrations.

**Correction from Phase 1**: Phase 1 reported 32 tools. Recount confirms 33 Tool() definitions in `list_tools()` and 33 dispatch branches in `call_tool()`.

## 2. Dead Handler Drift

4 handler methods exist in `mcp_server.py` but are NOT registered in `list_tools()` or dispatched in `call_tool()`:

| Handler | Line | Feature | Status |
|---------|------|---------|--------|
| `detect_untracked_work_enhanced_tool()` | 3076 | F1-Enhanced (E1-E4) | DEAD — complete implementation, not registered |
| `initialize_session_tool()` | 3262 | F002 | DEAD — complete implementation, not registered |
| `get_multi_session_dashboard_tool()` | 3338 | F002 | DEAD — complete implementation, not registered |
| `get_session_info_tool()` | 3397 | F002 | DEAD — complete implementation, not registered |

**Code has duplicate except block**: `detect_untracked_work_enhanced_tool` has two `except ImportError` blocks (lines 3244 and 3252). The second is unreachable.

**Impact**: Session management (F002) is fully implemented but completely inaccessible. The enhanced untracked work detection (E1-E4) is also implemented but unreachable.

## 3. Dual Codebase Divergence

**Critical architectural drift**: Two completely separate "Serena" implementations exist.

| Aspect | `services/serena/` | `docker/mcp-servers-source/serena/` |
|--------|-------------------|-------------------------------------|
| Lines of code | 54,638+ | ~135 (wrapper.py) |
| Tool count | 33 | UNKNOWN (upstream oraios/serena) |
| Transport | stdio | SSE (via mcp-proxy) |
| Intelligence engine | 27 modules | None (upstream code) |
| ConPort integration | Yes | No |
| ADHD features | Comprehensive | UNKNOWN |
| Dockerfile | None | Yes |
| compose.yml | Not referenced | Referenced |
| Port | N/A (stdio) | 3006 (SSE), 4006 (info) |

### compose.yml Path Mismatch
```yaml
# compose.yml says:
build:
  context: ./docker/mcp-servers/serena  # This directory does NOT exist

# Actual Dockerfile location:
docker/mcp-servers-source/serena/Dockerfile
```

The compose.yml references `./docker/mcp-servers/serena` but the Dockerfile is at `docker/mcp-servers-source/serena/`. This is a broken reference.

### Impact
- Docker `docker compose up serena` builds the upstream oraios/serena wrapper, NOT the dopemux services/serena/ implementation
- The 33-tool surface is only available via local stdio execution
- No Docker deployment path exists for the services/serena/ codebase
- CI/CD would deploy the upstream, not dopemux, Serena

## 4. Docstring vs Code Drift

| Claim (docstring/comment) | Actual (code) |
|---------------------------|---------------|
| "21+ tools" (line 10) | 33 tools registered |
| "24 tools" (line 5330) | 33 tools dispatched |
| "31-component" (line 4) | 27 intelligence modules + 43 feature modules |
| "3 tiers" (line 10) | 4 effective tiers + features + files |
| `total_available: 20` (line 1608) | 33 tools available |
| `total_planned: 21` (line 1609) | 33+ (with dead handlers: 37) |
| `semantic_search` listed as deferred (line 1607) | `find_similar_code` implements this |

## 5. Feature Flag Drift

| Feature | Expected Default | Actual Default | Source |
|---------|-----------------|----------------|--------|
| ADHD Engine integration | Configurable | Lazy-loaded, fails silently | `mcp_server.py:74` |
| Quiet hours | `enabled: false` | Defaults from storage | `untracked_work_storage.py` |
| ConPort connection | Required | Optional, graceful degradation | `_ensure_conport_client()` |
| LSP bypass threshold | Configurable | Hardcoded 5000 | `mcp_server.py:425` |

## 6. Schema vs Code Drift

### Intelligence Database
- `schema.sql` defines 6 tables with full schema
- No evidence of automatic migration at startup
- `schema_manager.py` exists but no startup trigger found in `mcp_server.py`
- **Risk**: Tables may not exist if database was never initialized

### ConPort Integration
- `conport_client_unified.py` hardcodes default credentials (`dopemux_age_dev_password`)
- Production credentials would need environment variable override
- No connection retry/backoff logic visible

## 7. Test Coverage Drift

| Test File | What It Tests | Alignment with Code |
|-----------|---------------|---------------------|
| `tests/test_serena_http.py` | HTTP health, metrics | Aligned with `http_server.py` |
| `tests/test_multi_workspace.py` | Workspace resolution | Aligned with `multi_workspace_wrapper.py` |
| `intelligence/test_database.py` | DB operations | Aligned with `intelligence/database.py` |
| `intelligence/integration_test.py` | Full integration | Broad coverage |

**Missing test coverage**:
- No tests for any of the 33 MCP tools directly
- No tests for `call_tool()` dispatch
- No tests for dead handlers
- No tests for ADHD Engine integration
- No tests for ConPort client adapter
- No tests for navigation cache

## 8. Version String Drift

| Location | Version | Notes |
|----------|---------|-------|
| `__init__.py:5` | `"2.0.0"` | Module version |
| `PKG-INFO` | `0.1.0` | Package metadata |
| Server name | `serena-v2` | In MCP registration |
| Docstring | `"Phase 2"` | Development phase |

The module version (2.0.0) and package version (0.1.0) are inconsistent.
