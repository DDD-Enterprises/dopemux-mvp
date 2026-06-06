# TP-DCP-MCP-RO-0006 Embedded Audit

**Packet:** TP-DCP-MCP-RO-0006 — Dope Context And Task Orchestrator Read Adapters
**Branch:** `dcp/chatgpt-mcp-ro-0006-dope-context-and-task-orchestrat`
**Base SHA:** `a3aa7db028e4d088b347bb0f2e67a1a0179e1d9b`
**Auditor:** claude-sonnet-4-6 subagent
**Date:** 2026-06-06

---

## A. dope-context Transport Decision Challenge

**Claim:** dope-context MCP JSON-RPC transport is not reachable from the facade's
`ReadOnlyHttpClient`. All three dope-context tools (search_code, docs_search,
get_index_status) are wired as fail-closed BLOCKED.

**Evidence inspected:**

1. `services/dope-context/src/mcp/server.py` — tools exposed exclusively via
   `@mcp.tool()` decorators (lines 991, 1362, 1506, 1876, 2223). No REST routes
   at `/search/code`, `/search/docs`, or `/index/status`.
2. `services/dope-context/src/mcp/server.py:149` — custom-route decorators for
   `/health` and `/info` are **commented out** (`# # @mcp.custom_route`). The
   server exposes only the FastMCP MCP JSON-RPC endpoint at `/mcp`.
3. `compose.yml` — `MCP_SERVER_PORT=3010` triggers `transport='http'` in
   `_resolve_transport_runtime()`, which means FastMCP serves MCP-over-HTTP at
   `/mcp` — **not** REST.
4. `services/dcp-readonly-facade/src/dcp_facade/http_client.py` — `ReadOnlyHttpClient`
   speaks REST (GET + explicit POST to a fixed path allowlist). It has no MCP
   JSON-RPC client capability.

**Counterargument considered:** Could the facade implement a minimal MCP JSON-RPC
wrapper over `ReadOnlyHttpClient`? Answer: yes, but (a) it is out of scope for a
"minimal correct change" in Phase 1; (b) the TP explicitly says "STOP IF:
dope-context requires search_all to produce useful results" (it doesn't in Phase 1);
(c) the architecture's fail-closed posture (§16) supports BLOCKED over fabrication.

**Decision:** Path 2 — fail-closed. The adapter raises `ReadOnlyHttpError` with an
explicit transport explanation. The tools.py layer intercepts and emits a BLOCKED
envelope with `limitations=["dope-context exposes tools via MCP JSON-RPC at /mcp;
facade speaks REST only — bridge pending Phase 2"]`. This is honest, non-fabricated,
and forward-compatible (Phase 2 fills in the implementation).

**Verdict: CORRECT.** The fail-closed path is the only honest option given the
current transport boundary.

---

## B. task-orchestrator Authority Boundary Challenge

**Claim:** `get_workflow_status_snapshot` is labelled `AUTHORITY_CANONICAL` for
workflow-view data, but the permanent limitation note
"task-orchestrator status is workflow-view authority only, not PM-metadata truth"
is always present.

**Challenge:** Isn't `AUTHORITY_CANONICAL` misleading if task-orchestrator is only
"workflow-view" and not "PM truth"?

**Response:** The architecture (§17) assigns `CANONICAL` to task-orchestrator queue
and blockers because they are authoritative for *what they are* — the workflow
execution state (queue, blockers, state transitions). They are NOT authoritative
for PM metadata (business goals, specs, PRD truth), which lives in ConPort. The
distinction is:
- `CANONICAL` = this is the authoritative source for THIS data type.
- "workflow-view only" = the data type itself is limited to execution state.

Both are true simultaneously. The limitation note prevents callers from treating
workflow state as PM truth. This matches the architecture's intent and the TP
invariant: "Task-orchestrator status is workflow-view only, not PM metadata truth."

**Verdict: CORRECT.** CANONICAL + limitation note is the right combination.

---

## C. /workflow/state Classification Challenge

**Claim:** `/api/projects/{project_id}/workflow/state` is classified
CONFIRMED_READ_ONLY and included in `get_workflow_status_snapshot`.

**Evidence:**
1. `services/task-orchestrator/app/api/project_workflow.py:385` —
   `@router.get("/state", response_model=WorkflowStateResult)` — confirmed GET.
2. `src/dopemux/pm/adapters/orchestrator.py:48` — existing PM adapter calls this
   route, confirming it is a live, reachable endpoint.
3. No POST, no write operation, no side-effect mechanism observed in the route handler.

**Risk considered:** The route was not in the TP-DCP-MCP-RO-0001 inventory. Could
it have side effects the inventory would have caught?

**Counter-evidence:** The handler at line 385 returns `WorkflowStateResult` — a
snapshot model. The existing PM adapter already reads it without side effects in
production. The `WorkflowStateResult` model contains `allowed_transitions` (metadata
about what transitions are *possible*, not an invocation of them) and linked IDs.

**Verdict: CORRECT to classify CONFIRMED_READ_ONLY and include.** Residual risk:
the 0001 inventory gap is not retroactively fixed (acceptable — 0001 is a committed
artifact). The gap is documented in §13 and §20 of ARCHITECTURE.md.

---

## D. Forbidden Route Grep Analysis

**Command:** `rg -n "search_all|index_workspace|..." services/dcp-readonly-facade`

**All hits are acceptable:**

| File | Line(s) | Context | Verdict |
|---|---|---|---|
| `route_manifest.py` | 44, 56-58 | Pre-existing DENIED_TOKENS/DENIED_ROUTES data | ACCEPTABLE — denylist definitions |
| `dope_context.py` | 27-35 | Module docstring denial documentation | ACCEPTABLE — prose, not callable |
| `task_orchestrator.py` | 105 | "allowed transitions" — describes the `allowed_transitions` field in the state response schema | ACCEPTABLE — docstring, no route string |
| `tools.py` | 526 | "workflow transition endpoints (MUTATING)" — docstring denial note | ACCEPTABLE — prose, not route string |
| `tests/test_packet_0006.py` | 11-359 | Denial assertion tests (MUST reference tokens to assert against) and fixture data | ACCEPTABLE — tests |

**No forbidden tokens appear in executable call paths.** The grep finds only
documentation, denylist definitions, and tests. Implementation is clean.

---

## E. Overall Verdict

**PASS_WITH_RISKS**

### Non-blocking risks (acknowledged, not blocking)

1. **dope-context BLOCKED in Phase 1:** `search_code_docs` and `get_index_status`
   always return BLOCKED. This is honest and intentional (transport not bridged),
   but callers receive no live data from these tools. Phase 2 must deliver the
   transport bridge to unlock value.

2. **get_index_status PROPOSED-only:** Not in the discovery inventory. Wired as
   fail-closed in Phase 1 but carries a dual-limitation (transport + inventory gap).
   Both must be resolved before Phase 2 can expose it.

3. **task-orchestrator project_id fallback:** When the registry profile does not
   set `task_orchestrator_project_id`, the facade falls back to the facade
   `project_id`. This may not match the actual task-orchestrator project routing
   in all deployments. Operators should set `task_orchestrator_project_id` in the
   registry profile explicitly.

4. **0001 inventory gap not retroactively fixed:** `/workflow/state` is classified
   here but the 0001 inventory artifact is not modified (it is a committed proof
   artifact). Future packets or a manifest refresh should reconcile this.

### Blocking risks: NONE

All TP invariants are satisfied:
- dope-context hits are DERIVED (or BLOCKED) — never CANONICAL without exact source.
- task-orchestrator is workflow-view only — permanent limitation in every envelope.
- Caller cannot supply backend route or project_id outside registry binding.
- Unavailable backend returns PARTIAL/BLOCKED — never fabricated data.
- search_all denied — not reachable from any adapter call path.
- index/sync/clear/autonomous routes denied — no callable invocations in adapter.
- transition and PM write routes denied — not in task_orchestrator adapter source.
- No bridge routing.
- No generic search/fetch.
- Tests pass (108 passed, 1 skipped live test).
