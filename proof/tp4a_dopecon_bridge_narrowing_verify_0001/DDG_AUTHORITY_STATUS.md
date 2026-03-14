# DDG Authority Status: dopecon-bridge

**Date:** 2026-03-12
**Status:** **PROXIED - NON-AUTHORITATIVE**

## Evidence of Narrowing
The bridge legacy "Dope Decision Graph" (DDG) logic has been narrowed to a read-only compatibility proxy.

### 1. Code-Level Redirection
The `ddg_router` (prefix `/ddg`) no longer references local SQLite or PG tables for decisions. Instead, it uses `conport_client` to fulfill requests:
- `GET /ddg/decisions` -> `conport_client.list_decisions`
- `GET /ddg/search` -> `conport_client.search_decisions`

### 2. No Local Mutation
There is **no active route** for `/ddg` that allows writes (POST/PUT/PATCH). All decision writes must now flow through either the `/kg/decisions` proxy or directly to the ConPort service.

### 3. Data Flow
All responses are normalized using the `_normalize_decision_list` and `_normalize_search_results` helpers, which explicitly label the source as `"conport"`.

## Final Verdict
Local DDG authority is **non-existent**. The bridge acts purely as a proxy for the canonical ConPort backend.
