# DopeconBridge Active Endpoint Inventory

**Date:** 2026-03-12
**Source of Truth:** `services/dopecon-bridge/dopecon_bridge/routes.py`
**Narrowing Status:** Verified

## Active Routes Summary
Total Active Endpoints: 23

### 1. Health & Root
- `GET /`: Service information (Architecture: adapter-only-active-runtime)
- `GET /health`: Service health check (MCP and ConPort status)

### 2. Authentication
- `POST /auth/token`: Login
- `POST /auth/refresh`: Token refresh

### 3. Event Bus Integration
- `POST /events`: Publish event (Authenticated)
- `GET /events/stream`: SSE subscription
- `GET /events/history`: Stream history
- `GET /events/{stream:path}`: Stream info
- `POST /events/tasks-imported`: Convenience publisher (Authenticated)
- `POST /events/session-started`: Convenience publisher (Authenticated)
- `POST /events/progress-updated`: Convenience publisher (Authenticated)

### 4. Tasks (Legacy/Blocked - Fail-Closed)
- `POST /tasks/parse-prd`: BLOCKED (canonical workflow adjudication required)
- `GET /tasks/next/{project_id}`: BLOCKED (Task Orchestrator required)
- `PATCH /tasks/{task_id}/status`: BLOCKED (Task Orchestrator adjudication required)

### 5. PM Routing (Leantime Proxy)
- `POST /pm`: PM adapter routing (Authenticated). Proxies to `leantime-bridge`.

### 6. ConPort Proxy (KG)
- `POST /kg/custom_data`: ConPort write proxy
- `GET /kg/custom_data`: ConPort read proxy
- `POST /kg/decisions`: ConPort write proxy
- `GET /kg/decisions`: ConPort read proxy
- `POST /kg/progress`: ConPort write proxy
- `GET /kg/progress`: ConPort read proxy

### 7. DDG Compatibility (ConPort Backed)
- `GET /ddg/decisions`: Decision list (Proxies to ConPort)
- `GET /ddg/search`: Decision search (Proxies to ConPort)

## Authority Verdict
The bridge explicitly rejects local task mutations and proxies all project data to ConPort or Leantime. No local task state is treated as authoritative.
