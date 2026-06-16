---
id: DMX-CONPORT-OPTIMAL-101-PROOF
title: "Proof Bundle: ConPort Server Bring-Up Smoke"
type: proof-bundle
tp_id: DMX-CONPORT-OPTIMAL-101
branch: feat/conport-optimal-series
date: 2026-06-16
executor: worktree-dopemux-mvp-feat/conport-optimal-series
---

# DMX-CONPORT-OPTIMAL-101 Proof Bundle

**Task**: Bring up ConPort service via docker compose and verify REST health endpoint and SSE wrapper reachability.

---

## Acceptance Criteria Verdicts

| Criterion | Result |
|-----------|--------|
| `GET http://localhost:3004/health` returns HTTP 200 | PASS |
| Health JSON shows db + redis healthy | PASS |
| SSE wrapper on :3005 responds | PASS |
| Container in running/healthy state | PASS |

**Overall verdict: PASS**

---

## S1: Preflight

- Repo root: `/Users/hue/code/dopemux-mvp`
- Branch: `feat/conport-optimal-series`
- Repo marker: `.dopetaskroot` present
- Origin: `DDD-Enterprises/dopemux-mvp`

---

## S2: Docker Compose Bring-Up

### Initial state (before restart)

Container `mcp-conport` was already running but UNHEALTHY. Root cause: on first startup, `enhanced_server.py` ran `psql -v ON_ERROR_STOP=1 -f /app/schema.sql`, which failed at line 289 (`GRANT ALL PRIVILEGES ... TO dopemux`) because only the `dopemux_age` superuser role exists. This caused `enhanced_server.py` to exit, leaving only `server.py` (port 3005) alive.

**Resolution (ops-only, no schema.sql modification):** The schema had been partially applied successfully — `workspace_contexts` and all 12 tables were present in the database. A `docker compose restart conport` allowed `enhanced_server.py` to find `workspace_contexts` on the second startup, skip `psql` re-application entirely, and start cleanly.

```
$ docker compose restart conport
Container mcp-conport Restarting
Container mcp-conport Started
```

### docker compose ps output

```
NAME          IMAGE             COMMAND                  SERVICE   CREATED          STATUS                     PORTS
mcp-conport   dopemux-conport   "bash start_with_inf…"   conport   11 minutes ago   Up 48 seconds (healthy)    0.0.0.0:3004-3005->3004-3005/tcp, [::]:3004-3005->3004-3005/tcp, 0.0.0.0:4004->4004/tcp, [::]:4004->4004/tcp
```

### Startup log (post-restart, key lines)

```
INFO:__main__:✅ PostgreSQL connection pool established
INFO:__main__:✅ Database schema present (workspace_contexts found)
INFO:__main__:✅ Redis connection established
INFO:integration_bridge_client:✅ DopeconBridge client initialized
INFO:__main__:✅ Enhanced ConPort API available at http://0.0.0.0:3004
INFO:__main__:Started server process [9]
INFO:__main__:Uvicorn running on http://0.0.0.0:3005 (Press CTRL+C to quit)
```

---

## S3: Smoke Verification

### :3004/health — HTTP code

```
$ curl -s -o /dev/null -w '%{http_code}' http://localhost:3004/health
200
```

**Exit code: 0. Result: PASS**

### :3004/health — JSON response

```json
{
  "status": "healthy",
  "service": "conport-enhanced",
  "port": 3004,
  "database": "healthy",
  "redis": "healthy",
  "timestamp": 116496.903456603
}
```

**database: healthy, redis: healthy. Result: PASS**

### :3005 SSE — port listening

```
$ curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://localhost:3005/sse
200
```

**SSE endpoint returned HTTP 200. Result: PASS**

### Optional: /api/context endpoint

```
$ curl -s -o /dev/null -w '%{http_code}' 'http://localhost:3004/api/context/%2FUsers%2Fhue%2Fcode%2Fdopemux-mvp'
500
Response: {"error": "column \"instance_id\" does not exist"}
```

**Note**: This 500 is a pre-existing bug (DMX-CONPORT-OPTIMAL-203 scope: fix workspace relationships traversal). It does not affect bring-up acceptance criteria.

---

## S4: Known Bug Observed

- **Bug**: `schema.sql` line 289-291 GRANTs privileges to role `dopemux` which does not exist in postgres (only `dopemux_age` exists). This causes the initial cold-start to fail with `psql: ERROR: role "dopemux" does not exist`.
- **Impact**: First-start or fresh-database scenarios will always leave `enhanced_server.py` crashed after initial schema apply. A restart is required.
- **Workaround applied**: `docker compose restart conport` (schema tables already existed from partial apply).
- **Fix scope**: Covered by DMX-CONPORT-OPTIMAL-203 or a dedicated schema fixup packet. This packet (101) is ops-only and does not modify `schema.sql`.

---

## Validation Buckets

| Check | Status | Notes |
|-------|--------|-------|
| `GET /health` HTTP 200 | PASS | |
| Health JSON db=healthy | PASS | |
| Health JSON redis=healthy | PASS | |
| :3005 SSE listening | PASS | HTTP 200 |
| Container docker status=healthy | PASS | |
| schema.sql unmodified | PASS | Invariant upheld |
| No production data modified | PASS | |
| No migration files altered | PASS | |

---

## Files Touched

- `claudedocs/proof/DMX-CONPORT-OPTIMAL-101/DMX-CONPORT-OPTIMAL-101-PROOF.md` (this file, new)

No source code was modified. All changes are ops-level (container restart).

---

## Git State

- Branch: `feat/conport-optimal-series`
- Working tree: clean (proof file only added)
