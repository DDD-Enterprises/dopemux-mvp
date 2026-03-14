# ConPort Preferred Canonical Surface Decision

**Date:** 2026-03-12
**Decision:** **REST `/api/*` is the preferred canonical PM-plane integration surface.**

---

## Decision

> The HTTP REST surface at `/api/*` (port 3004) is designated as the canonical integration surface
> for PM-plane use. FastMCP is the preferred agent ergonomics wrapper. JSON-RPC is compatibility-only
> until parity gaps are closed.

---

## Rationale

### 1. Broadest contract

REST exposes all 21 logical operations, including:
- Phase 2 features (`unified-search`, `workspace-relationships`)
- Custom data operations (`save_custom_data`, `get_custom_data`, `delete_custom_data`)
- All 9 core PM operations

FastMCP exposes 13 tools (missing search, custom_data, Phase 2 features).
JSON-RPC exposes 13 methods (missing workspace_summary from dispatch; search undiscoverable).

### 2. Already the authoritative backend

Both FastMCP wrappers (`server.py`, `conport_mcp_stdio.py`) and the JSON-RPC handler
(`enhanced_server.py _dispatch_tool()`) delegate internally to the REST endpoints.
REST is the authoritative source of truth, not a convenience layer.

### 3. Explicit payload discipline

REST uses clear HTTP verbs (GET, POST, PUT, DELETE) with explicit request/response schemas.
No runtime dispatch map drift. No hidden name-translation layers.

### 4. Single-location discoverability

All routes enumerated in `setup_routes()` (enhanced_server.py:235–280).
Full surface is auditable without reading multiple dispatch maps or wrapper files.

### 5. Testability

REST endpoints are independently testable via curl/pytest/Postman.
No protocol overhead. No MCP session state required.

### 6. Stability

REST surface has been in production longest. Lowest surface area for hidden behavior changes.
Wrapper surfaces add indirection that can drift.

### 7. Direct mapping

Each logical operation maps 1:1 to a REST endpoint. No naming drift (the `log_decision`
topic/decision→summary wrapper translation was a bug, not a feature, and is now repaired).

### 8. No discovery gaps

All operations are discoverable. Unlike JSON-RPC (workspace_summary missing) and FastMCP
(search missing).

---

## Role assignments

| Surface | Role |
|---------|------|
| **REST `/api/*`** | **Canonical integration surface.** Use for PM-plane service-to-service calls. Test against REST for correctness. |
| **FastMCP (SSE + stdio)** | **Agent ergonomics wrapper.** Use when agents need MCP tool calls. Acceptable if semantically aligned to REST. Wrapper drift is a bug. |
| **JSON-RPC `/mcp`** | **Compatibility-only.** Do not choose as primary PM-plane surface until workspace_summary dispatch gap and search discoverability gap are closed. |

---

## Constraint: FastMCP wrapper discipline

FastMCP is acceptable for agent-facing use, with these constraints:
- Wrapper drift is a bug to fix, not a feature to work around
- FastMCP wrappers must stay semantically aligned to REST
- Any new FastMCP tool must have a corresponding REST endpoint it delegates to
- Do not add FastMCP tools that perform logic the REST backend does not support

---

## Constraint: JSON-RPC parity path

JSON-RPC can be promoted to canonical when:
1. `conport_workspace_summary` is added to `_dispatch_tool()` and `_get_tool_schemas()`
2. `conport_search_content` is added to `_get_tool_schemas()` for discoverability
3. All operations in dispatch map appear in tool schema discovery

Until then: JSON-RPC is compatibility-only.

---

## What this decision does NOT change

- ConPort authority over decisions/progress/context is unchanged
- No surface redesign required
- No REST API changes required
- No migration of existing consumers required

This is a documentation and integration guidance decision, not an implementation change.
