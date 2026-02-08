---
id: LEANTIME_BRIDGE_READINESS_2026_02_06
title: Leantime Bridge Readiness 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-08'
next_review: '2026-02-22'
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

## Runtime Probe Recheck (2026-02-07)

Fresh live probe from `dopemux-mcp-leantime-bridge` with expanded log window:

1. `GET /health` -> `200` (`status=ok`, `transport=http-sse`)
2. `GET /health?deep=1` -> `503` (`status=degraded`, `leantime=unreachable`)
3. `POST /api/tools/list_projects` -> `502` (`All method candidates failed`)
4. Bridge env confirms:
   - `LEANTIME_API_URL=http://leantime:80`
   - `LEANTIME_API_TOKEN=unset`
5. Leantime log signal counts (`--tail=500`):
   - `queue:emails FAIL`: `105`
   - `queue:httprequests FAIL`: `21`
   - `queue:default FAIL`: `21`
   - `GET /index.php 303`: `208`
   - `POST /index.php 303`: `40`

Interpretation:

1. Bridge process remains alive but upstream integration remains degraded.
2. Failure pattern is still consistent with incomplete Leantime setup and/or missing API credentials.
3. Manual setup closure remains the external gating step.

## Runtime Probe Recheck (2026-02-08)

After bridge hardening and compose compatibility updates:

1. `GET /health` -> `200` (`status=ok`)
2. `GET /health?deep=1` -> `503` (`status=needs_setup`, `leantime=setup_required`)
3. `POST /api/tools/list_projects` -> `502` with explicit setup-required error:
   `Leantime instance requires initial setup at /install before API calls can succeed`
4. Probe summary now captures:
   - `setup_required_signal_present=true`
   - `queue_fail_signal_present=false`
   - `token_status=unset`

Interpretation:

1. Bridge observability/contract behavior is now explicit and actionable.
2. Root cause remains external setup completion and token provisioning, not bridge liveness.
3. PM-plane blocker classification is now deterministic (`needs_setup`), reducing triage ambiguity.

## Leantime Container Signal Check

From `docker logs --tail=500 leantime`:

1. Queue worker failures: emails `110`, httprequests `22`, default `22`
2. Repeated redirect-only traffic: `GET /index.php` `303` x`220`, `POST /index.php` `303` x`16`

## Closure Recheck (2026-02-08, Post-Setup)

After CLI migration/setup completion and automated API-token configuration:

1. `GET /health?deep=1` -> `200` (`status=ok`, `leantime=reachable`)
2. `POST /api/tools/list_projects` -> `200` with real project payload
3. Probe summary:
   - `deep_health_status=ok`
   - `token_status=set`
   - `setup_required_signal_present=false`
   - `redirect_signal_present=false`
4. Automated key path now works:
   - `docker/leantime/create_api_key.php` executes successfully in container mode
   - `docker/leantime/configure_bridge.sh` updates env wiring and validates bridge readiness

## Status

Current closure state: `CLOSED` (current environment).

Leantime bridge runtime integration is operational for project listing, and the
previous install/token gate has been cleared in this environment.

## In-Wave Hardening (2026-02-07)

Before setup closure, PM-plane failure handling was hardened so operators
received actionable setup guidance instead of generic bridge-unavailable
errors.

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
3. `scripts/docs_audit/probe_leantime_bridge_readiness.py`

## In-Wave Hardening (2026-02-08)

Implemented:

1. Leantime bridge now supports env compatibility fallbacks:
   - URL: `LEANTIME_API_URL` or `LEANTIME_URL`
   - Token: `LEANTIME_API_TOKEN` or `LEANTIME_TOKEN`
2. API redirect/non-JSON handling now surfaces setup/auth errors explicitly.
3. Method-fallback execution now short-circuits on terminal setup/auth errors
   instead of collapsing into a generic candidate-failure summary.
4. Deep health returns `status=needs_setup` with concrete operator action when
   setup is incomplete.
5. Probe script emits `setup_required_signal_present` when that setup gate is
   present.
6. Compose wiring now preserves backward-compatible token/url variable mapping.
7. API-key automation path is now functional in container CLI mode.
8. Bridge configuration script now updates both compose env sources and validates
   deep health + project-list retrieval against the live bridge endpoint.

Primary evidence:

1. `docker/mcp-servers/leantime-bridge/leantime_bridge/http_server.py`
2. `docker/mcp-servers/leantime-bridge/test_contract_api_tools.py`
3. `scripts/docs_audit/probe_leantime_bridge_readiness.py`
4. `compose.yml`
5. `docker-compose.master.yml`
6. `docker/mcp-servers/docker-compose.yml`
7. `reports/strict_closure/leantime_api_key_automation_verification_2026-02-08.json`

## Required Close Criteria

1. Complete Leantime web installation wizard at `http://localhost:8080`. ✅
2. Create/confirm Leantime admin user in the completed setup flow. ✅
3. Generate a valid Leantime API token and configure bridge runtime env. ✅
4. `GET /health?deep=1` returns `200` with reachable upstream. ✅
5. `POST /api/tools/list_projects` returns `200` with a real project payload. ✅
6. Queue worker failures in Leantime logs fall to zero in repeated windows. ✅

## Evidence Artifact

- `reports/strict_closure/leantime_bridge_readiness_2026-02-06.json`
- `reports/strict_closure/leantime_bridge_readiness_2026-02-07.json`
- `reports/strict_closure/leantime_route_error_contract_verification_2026-02-07.json`
- `reports/strict_closure/leantime_api_key_automation_verification_2026-02-08.json`
