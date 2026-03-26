# TP5A Completion Report: ConPort Full Surface Drift

**Packet:** TP5A-CONPORT-FULL-SURFACE-DRIFT-0001
**Date:** 2026-03-12
**Verdict:** COMPLETE

---

## Acceptance Criteria Checklist

- [x] All three surfaces are inventoried
- [x] Unified logical operation list exists (21 operations)
- [x] Equivalence matrix exists (SURFACE_EQUIVALENCE_MATRIX.csv)
- [x] Drift matrix exists (DRIFT_MATRIX.md, 6 open drift cases)
- [x] Dark methods are explicitly listed (4 in DARK_METHOD_INVENTORY.md)
- [x] Preferred canonical surface is explicitly chosen (REST)
- [x] Invariant gaps are documented (5 in INVARIANT_GAPS.md)
- [x] Packet does not confuse MCP pass-through success with full-surface alignment

---

## Supervisor Output

| Metric | Value |
|--------|-------|
| **FastMCP operation count** | 13 |
| **JSON-RPC operation count** | 13 (12 discoverable via tools/list; conport_search_content undiscoverable) |
| **REST operation count** | 21 |
| **Total logical operation count** | 21 |
| **Number of drift cases** | 6 |
| **Number of dark methods** | 4 (3 admin-only operations + 1 undiscoverable JSON-RPC method) |
| **Preferred canonical surface** | **REST `/api/*` (port 3004)** |
| **Unresolved invariant gaps** | 5 (auth hardening × 2, provenance × 1, contract × 1, deployment × 1) |
| **Proof bundle path** | `proof/tp5a_conport_full_surface_drift_0001/` |

---

## Key Findings

### 1. REST is canonical — not just convenient
FastMCP and JSON-RPC wrappers both delegate to REST. REST is the backend, not the alias.

### 2. JSON-RPC has two confirmed parity gaps
- `workspace_summary`: missing from `_dispatch_tool()` dispatch map (enhanced_server.py:1736–1750)
- `search_content`: in dispatch map but absent from `_get_tool_schemas()` — undiscoverable

Do not use JSON-RPC as PM-plane canonical surface until these are closed.

### 3. FastMCP is a valid agent ergonomics wrapper — with constraints
FastMCP exposes 13 tools, covers all 9 core PM operations + workspace_summary. Missing: search.
Wrapper drift (log_decision topic→summary, log_progress default status) has been repaired.
FastMCP is acceptable for agent use when semantically aligned to REST.

### 4. Dark methods are present but accessible
fork_instance, promote, promote_all are exposed on all three surfaces and are discoverable via
`tools/list`. They are not access-controlled. Any MCP agent can call them.
Document as admin-only. Do not include in PM-plane agent instructions.

### 5. 5 invariant gaps — none are PM-plane correctness breaks
All 5 gaps are operational hardening or documentation issues.
ConPort's canonical authority over decisions/progress/context is functionally correct.

---

## Proof Bundle Files

| File | Contents |
|------|---------|
| `SURFACE_INVENTORY_REST.md` | 21 REST operations with method/path/params |
| `SURFACE_INVENTORY_FASTMCP.md` | 13 FastMCP tools with params/descriptions |
| `SURFACE_INVENTORY_JSONRPC.md` | 13 JSON-RPC methods with discoverability status |
| `SURFACE_EQUIVALENCE_MATRIX.csv` | 21 logical operations × 3 surfaces with confidence and notes |
| `DRIFT_MATRIX.md` | 6 open drift cases with evidence, impact, remediation |
| `DARK_METHOD_INVENTORY.md` | 4 dark methods (3 admin-only + 1 undiscoverable JSON-RPC) |
| `PREFERRED_SURFACE_DECISION.md` | REST chosen as canonical; FastMCP as wrapper; JSON-RPC compatibility-only |
| `INVARIANT_GAPS.md` | 5 invariant gaps: auth hardening × 2, provenance, contract, deployment |
| `COMPLETION_REPORT.md` | This file |

---

## What This Packet Does NOT Resolve

- Auth hardening on ConPort endpoints (separate hardening task)
- JSON-RPC parity gap fix (separate code change)
- FastMCP search wrapper addition (separate code change)
- Phase 2 feature stabilization (roadmap item)
- AGE deployment validation (operational item)

These are follow-up tasks, not gaps in this proof bundle's scope.
