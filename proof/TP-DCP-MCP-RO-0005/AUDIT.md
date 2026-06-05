# Audit — TP-DCP-MCP-RO-0005 (ConPort + dope-memory Read Adapters)

Auditor focus per packet `embedded_audit`. Verdict: **PASS_WITH_RISKS** (non-blocking residual risks; HIGH-risk security review completed and findings fixed).

## 1. Is any POST permission over-broad?

No. POST is reachable **only** via `ReadOnlyHttpClient.post_read(path, json, allowed_read_paths)`, which rejects any path not in `DOPE_MEMORY_READ_PATHS = {"/tools/memory_search", "/tools/memory_replay_session"}`. There is no generic `request(method,...)` and no put/patch/delete on the client; `_default_transport` additionally asserts method ∈ {GET, POST}. The dope-memory adapter passes only those two paths. Denylist tests assert the allowlist is exactly those two and that the mutating `memory_correct` (+ reflection/store/mark-issue/link) paths are not constructible.

## 2. Could a caller hit ConPort mutation routes / dope-memory correction?

No. ConPort is reached only through GET adapters (`/api/decisions`, `/api/progress`, `/api/search/{ws}`); there is no POST path to ConPort anywhere in the adapter code. dope-memory mutations are blocked by the POST-read allowlist (§1). The denied route literals appear **only** in `route_manifest.py` (data) and tests — never in an adapter call path (verified by grep over `conport.py`/`dope_memory.py`/`http_client.py`/`tools.py`).

## 3. Are service profiles project-scoped (caller cannot pick workspace_id/base_url)?

Yes. The tools resolve the project via the 0004 fail-closed resolver, then read `base_url` + `workspace_id` from `project.service_profiles[name]`. The MCP caller supplies only `project_id` + tool params (query/status/session_id/top_k/mode) — never a URL, host, port, route, or workspace id. A missing/unbound profile → `BLOCKED` (capability unavailable). Tests assert `workspace_id` in the issued request comes from the registry, not the caller.

## 4. Fail-closed?

Yes. Unknown/disabled project → BLOCKED (0004 resolver); missing profile → BLOCKED; missing `session_id` → BLOCKED; backend error/timeout (`ReadOnlyHttpError`) → BLOCKED; non-2xx → PARTIAL with no body; all backend payloads pass through 0004 redaction before enveloping. Never fabricated data.

## PAL codereview (gpt-5.2, security, HIGH-risk gate)

Ran `pal/codereview` (security, external) on http_client / conport / dope_memory / route_manifest / tools. Findings + dispositions:

- 🔴 **Unbounded backend response size (DoS)** → FIXED: `_default_transport` streams the body with a `MAX_RESPONSE_BYTES` cap; oversize → `ReadOnlyHttpError` (fail closed).
- 🔴 **Parsing non-2xx bodies** → FIXED: JSON is parsed only when `resp.is_success`; non-2xx → `PARTIAL` with `data=None`.
- 🟠 **String-based loopback check** → FIXED: `_is_loopback` now uses `ipaddress.is_loopback` for IP literals (`127.0.0.0/8`, `::1`, IPv4-mapped loopback) and allows only `localhost` (trailing dot normalized) for names; `0.0.0.0`/`::`/routable IPs rejected.
- 🟠 **`workspace_id` path interpolation** → FIXED: `conport.search` percent-encodes the segment and rejects `/`/`..` (fail closed).
- 🟠 **`_join` allowed query/fragment** → FIXED: rejects `?`/`#`.
- 🟡 **Exception text in blocked_reasons** → FIXED: generic `"backend unavailable"` (no host/port/exception leak to the caller).
- 🟡 **Broad JSON except** → FIXED: narrowed to `ValueError`. **Query not normalized** → FIXED: `_norm_query` strips + caps at 256 chars.
- 🟢 **`[::1]` dead data / untyped `fetch`** → FIXED (ipaddress refactor removed the literal; `fetch: Callable[[], HttpResponse]`).

## Deviations / residual risks (non-blocking)

- **`services/registry.yaml` NOT updated** (packet `forbidden_files`); the facade remains an unregistered stdio MCP server — flagged for operator.
- **Sync HTTP in async MCP wrappers**: adapters use a sync httpx client (consistent with 0004 sync tools; trivially mockable). A brief event-loop block on a loopback call is acceptable for a Phase-1 local facade; async/threadpool deferred to hardening (0008).
- **DNS rebinding** is not addressable at this layer (base_url is a registry-owned literal host; we do not re-resolve). Acceptable for loopback-only.
- **Redaction is heuristic** defence-in-depth (may over-redact); reachability of `service_profiles` is exercised against a mocked transport (live tests are opt-in behind `DCP_FACADE_LIVE_TESTS=1`).
- **`httpx` optional**: imported lazily; tests inject a fake transport and make no live calls.
