# DRIFT REPORT — dope-memory

## 1. Tool Count Discrepancy

| Surface | Tool Count | Evidence |
|---------|-----------|----------|
| `dope_memory_main.py` routes | 10 | Lines 1089–1298 |
| `dope_memory_main.py` inline `DopeMemoryMCPServer` methods | 10 | Lines 137–728 |
| `dope_memory_main.py` root `GET /` listing | **7** | Lines 1072–1080 |
| `mcp/server.py` `DopeMemoryMCPServer` methods | **7** | Lacks `memory_generate_reflection`, `memory_reflections`, `memory_trajectory` |
| `services/dope-memory/mcp_stdio_adapter.py` | **3** | Only `memory_recap`, `memory_search`, `memory_store` |
| `docs/spec/dope-memory/v1/07-mcp-contracts.md` | **7** | Per Phase 1 inspection |
| Test files covering tools | ~10 | Various test files cover all 10 endpoints |

### Missing from root listing
The `GET /` endpoint lists only 7 tools:
```python
"tools": [
    "memory_search", "memory_store", "memory_recap",
    "memory_mark_issue", "memory_link_resolution",
    "memory_replay_session", "memory_correct",
]
```
**Missing:** `memory_generate_reflection`, `memory_reflections`, `memory_trajectory`

**Impact:** MCP clients that discover tools via `GET /` will not see Phase 2 tools. The routes themselves exist and are callable.

## 2. Two Divergent DopeMemoryMCPServer Classes

| Location | Tools | Runtime Authority |
|----------|-------|-------------------|
| `dope_memory_main.py` (inline) | 10 | **YES** — imported by FastAPI app |
| `mcp/server.py` (module) | 7 | **NO** — not imported by `dope_memory_main.py` |

Both define a class named `DopeMemoryMCPServer`. The `mcp/__init__.py` exports the 7-tool version, but `dope_memory_main.py` defines its own inline 10-tool version and does NOT import from `mcp/server.py`.

**Risk:** Developers editing `mcp/server.py` may believe they are modifying the runtime server. Changes there have no effect on the running service.

## 3. SSE Transport Not Implemented

| Configuration | Value | Code Evidence |
|---------------|-------|---------------|
| `.claude.json` | `"type": "sse", "url": "http://localhost:3020/mcp"` | No `/mcp` endpoint in `dope_memory_main.py` |

The server only exposes REST endpoints. No SSE, Server-Sent Events, or MCP JSON-RPC protocol endpoints are implemented.

**Impact:** Any MCP client configured to connect via SSE to `/mcp` will fail to connect.

## 4. Stdio Adapter Targets Wrong Port

| Setting | Expected | Actual |
|---------|----------|--------|
| Adapter target URL | `http://localhost:3020/tools` | `http://localhost:8096/tools` |

Source: `services/dope-memory/mcp_stdio_adapter.py:16`

The stdio adapter proxies to port 8096 (legacy WMA service), not to port 3020 (canonical dope-memory server). The adapter will either:
- Fail if WMA is not running
- Return WMA responses (different API contract) if WMA is running

## 5. Pydantic Model vs Method Signature Discrepancies

### memory_mark_issue

| Parameter | Pydantic Model (MemoryMarkIssueRequest) | Method Signature |
|-----------|----------------------------------------|------------------|
| `description` | `description: str` | `description: str` (positional) |
| `severity` | Not in Pydantic model | Not in method |
| `notes` | Not in Pydantic model | Not in method |

Phase 1 DISCOVERY_NOTES listed `severity` and `notes` as parameters. Code inspection shows the Pydantic model uses `description` instead. The method handler receives `description` from the Pydantic model but the method body only checks entry existence — the `description` parameter is accepted but not stored.

### memory_correct

| Parameter | Pydantic Model | Method Signature |
|-----------|---------------|------------------|
| `new_summary` | Not in Pydantic | Not in method |
| `new_details` | Not in Pydantic | Not in method |
| `new_outcome` | Not in Pydantic | Not in method |
| `reason` | Not in Pydantic | Not in method |
| `corrected_summary` | ✅ In Pydantic | ✅ In method |
| `corrected_tags` | ✅ In Pydantic | ✅ In method |
| `corrected_category` | ✅ In Pydantic | ✅ In method |
| `corrected_entry_type` | ✅ In Pydantic | ✅ In method |
| `corrected_outcome` | ✅ In Pydantic | ✅ In method |
| `idempotency_key` | ✅ In Pydantic | ✅ In method |

Phase 1 DISCOVERY_NOTES listed `new_summary`, `new_details`, `new_outcome`, `reason` as parameters. Code uses `corrected_*` naming convention instead.

### memory_generate_reflection

| Parameter | Pydantic Model | Method Signature |
|-----------|---------------|------------------|
| `window_start` | Not in Pydantic | Not in method |
| `window_end` | Not in Pydantic | Not in method |
| `window_hours` | ✅ `window_hours: int = 2` | ✅ `window_hours: int = 2` |

The Phase 1 notes listed `window_start` and `window_end` but the code uses `window_hours` to auto-compute the window.

## 6. Redaction Coverage

The `Redactor` class handles secrets comprehensively, but the `memory_mark_issue` endpoint does not pass the `description` through the redactor before (not) storing it. Since `description` is currently unused in persistence, this is a latent risk.

## 7. Docker Volume Mount vs WAL

In `compose.yml`, `DOPEMUX_SQLITE_JOURNAL_MODE=DELETE` is explicitly set, overriding the code default of `WAL`. This is because WAL mode can have issues with Docker bind-mount volumes across filesystems. This is an intentional configuration, not a bug, but it is undocumented.

## 8. Spec Document vs Code Alignment

| Spec Document | Claims | Code Reality |
|---------------|--------|--------------|
| `07_mcp_contracts.md` | 7 tools | 10 tools implemented (3 Phase 2 added after spec) |
| `02_data_model_sqlite.md` | Schema without provenance | Schema has provenance (added by migration v1.1.0) |
| `08_phased_roadmap.md` | Phase 2 as future | Phase 2 reflection + trajectory implemented |
| Registry (`registry.yaml`) | Category: `mcp` | Accurate — serves MCP-like tool endpoints |
| `.claude.json` | SSE transport | NOT implemented |

## 9. Summary of Stale Artifacts

| Artifact | Status | Recommended Action |
|----------|--------|-------------------|
| `mcp/server.py` | Shadowed, 7 tools | Delete or reconcile with inline 10-tool version |
| `services/dope-memory/mcp_stdio_adapter.py` | Targets port 8096 | Update to target port 3020 |
| `GET /` tool listing | Lists 7 tools | Add Phase 2 tools to listing |
| `.claude.json` SSE config | Non-functional | Either implement `/mcp` SSE endpoint or add MCP proxy |
| `docs/spec/dope-memory/v1/07-mcp-contracts.md` | 7 tools documented | Update to cover all 10 tools |
| WMA-era modules (`wma_core.py`, `bridge_adapter.py`, etc.) | Dead code for dope-memory | Consider extracting to separate directory or removing |
