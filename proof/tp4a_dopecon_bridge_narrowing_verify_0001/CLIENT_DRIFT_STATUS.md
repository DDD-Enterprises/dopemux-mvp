# Client Drift Status: dopecon-bridge

**Date:** 2026-03-12
**Status:** **ALIGNED - MINIMAL DRIFT**

## Inspection Findings
The shared client (`services/shared/dopecon_bridge_client/client.py`) was compared against the active runtime routes.

### 1. Alignment Successes
- **Narrowing:** The client has no methods for the blocked `tasks/` endpoints (`parse-prd`, `next-action`, etc.), preventing accidental use of non-canonical surfaces.
- **Surface Blocking:** Methods like `route_cognitive`, `related_decisions`, and `create_link` explicitly raise `DopeconBridgeError` for unsupported surfaces, matching the narrowing policy.
- **ConPort Proxying:** Client methods for custom data, decisions, and progress correctly target the `/kg/` and `/ddg/` proxy routes.

### 2. Identified Drift
- **Payload Field "entries" vs "progress":** In `get_progress_entries`, the client looks for `entries`. The server's `_normalize_progress_list` returns both `entries` and `progress` to maintain compatibility. **Status: Safe Compatibility.**
- **Auth Requirement:** The client supports the `Authorization` bearer token in its base configuration. The active runtime now requires this for `/route/pm` and `/events`.

### 3. Non-Canonical Coverage
No methods in the client were found to target dead or non-canonical "shadow" storage paths in the bridge.

## Final Verdict
The shared client is **Aligned** with the narrowed runtime.
