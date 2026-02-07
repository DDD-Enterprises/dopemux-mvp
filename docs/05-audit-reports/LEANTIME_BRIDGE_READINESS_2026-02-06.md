---
id: LEANTIME_BRIDGE_READINESS_2026_02_06
title: Leantime Bridge Readiness 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-07'
next_review: '2026-02-21'
status: draft
prelude: Runtime evidence for Leantime bridge integration readiness and manual-setup closure status.
---
# Leantime Bridge Readiness (2026-02-06)

## Scope

Closure evidence for the pending ConPort-missed item:

1. `Leantime manual setup completion`

## Runtime Probe Results

Bridge environment (`dopemux-mcp-leantime-bridge`):

1. `LEANTIME_API_URL=http://leantime:80`
2. `LEANTIME_API_TOKEN` is not set
3. `MCP_SERVER_PORT=3015`

Probe outcomes:

1. `GET /health` -> `200` (`status=ok`)
2. `GET /health?deep=1` -> `503` (`status=degraded`, `leantime=unreachable`)
3. `POST /api/tools/list_projects` -> `502` (`All method candidates failed`)

## Leantime Container Signal Check

From `docker logs --tail=500 leantime`:

1. Queue worker failures: emails `110`, httprequests `22`, default `22`
2. Repeated redirect-only traffic: `GET /index.php` `303` x`220`, `POST /index.php` `303` x`16`

## Status

Current closure state: `BLOCKED`.

Bridge process liveness is healthy, but real Leantime API integration is not yet operational for project listing. This keeps PM-plane integration below production-ready state.
ConPort historical TODO context remains accurate: Leantime containers are running and healthy, but manual web setup completion is still required before bridge API operations can succeed.
Historical task description: `Leantime containers are running and healthy - needs manual web setup completion: access http://localhost:8080 to complete installation wizard, create admin user, generate API token, then configure bridge`.

## In-Wave Hardening (2026-02-07)

While manual Leantime setup is still externally blocked, PM-plane failure handling
is now hardened so operators receive actionable setup guidance instead of generic
bridge-unavailable errors.

Implemented:

1. `MCPClientManager.call_tool()` now preserves upstream status/body context in
   502 error details.
2. Leantime-specific failures now include readiness hints:
   complete wizard at `http://localhost:8080`, verify credentials, and set
   `LEANTIME_API_TOKEN`.
3. Contract tests were added for both Leantime-hinted failures and non-Leantime
   upstream failure context preservation.

Primary evidence:

1. `reports/strict_closure/leantime_route_error_contract_verification_2026-02-07.json`
2. `services/dopecon-bridge/tests/test_leantime_route_contract.py`

## Required Close Criteria

1. Complete Leantime web installation wizard at `http://localhost:8080`.
2. Create/confirm Leantime admin user in the completed setup flow.
3. Generate a valid Leantime API token and configure bridge runtime env.
4. `GET /health?deep=1` returns `200` with reachable upstream.
5. `POST /api/tools/list_projects` returns `200` with a real project payload.
6. Queue worker failures in Leantime logs fall to zero in repeated windows.

## Evidence Artifact

- `reports/strict_closure/leantime_bridge_readiness_2026-02-06.json`
- `reports/strict_closure/leantime_route_error_contract_verification_2026-02-07.json`
