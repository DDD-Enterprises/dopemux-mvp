---
title: Leantime + Dopemux Production Gap Analysis
type: explanation
date: '2026-02-06'
status: active
id: leantime-dopemux-production-gap-analysis
owner: '@hu3mann'
last_review: '2026-02-06'
next_review: '2026-03-06'
author: '@codex'
prelude: Deep-dive on Leantime container integration, implementation status, and production hardening plan for Dopemux.
---

# Leantime + Dopemux Production Gap Analysis

## Scope

This document captures:
- Current Leantime integration architecture in Dopemux
- Features implemented versus planned/mentioned
- Production-readiness gaps
- Hardening work completed on 2026-02-06
- Remaining work to reach feature-complete, production-grade operation

## Current Integration Topology

1. Leantime runtime stack
- `docker/leantime/docker-compose.yml` (separate stack for Leantime + MySQL + Redis)
- `docker/leantime/plugins/Dopemux/*` (Leantime-side plugin code)

1. Leantime bridge service (PM plane)
- `docker/mcp-servers/leantime-bridge/leantime_bridge/http_server.py`
- Provides MCP/SSE integration and service discovery (`/sse`, `/messages/`, `/info`)

1. Cross-plane routing and PM adapters
- `services/dopecon-bridge/main.py` (`/route/pm`, `/route/leantime`)
- `services/shared/dopecon_bridge_client/leantime_adapter.py` calls PM route operations (`leantime.create_task`, `leantime.get_tasks`, etc.)

1. Orchestration consumers
- `services/task-orchestrator/*` and `src/integrations/*` consume Leantime data for ADHD-aware planning/sync.

## Planned and Mentioned Feature Surface

Across docs/code, the following capabilities are explicitly referenced:
- Create/list/update Leantime tickets
- Create/list projects and fetch project status/progress
- Milestone creation
- Sprint status updates
- Resource allocation
- Bidirectional PM ↔ Cognitive sync
- Service discovery (`/info`) for auto-configuration
- ADHD-oriented metadata and recommendations surfaced from Leantime context

## Hardening Completed (2026-02-06)

1. Leantime bridge execution compatibility
- Added JSON-RPC method fallback support across known Leantime method namespace/casing variants.
- Added argument normalization and aliasing for legacy callers:
- `create_task` -> `create_ticket`
- `list_tasks` -> `list_tickets`
- `update_ticket_status` -> `update_ticket`

1. REST compatibility endpoint for existing Dopemux callers
- Added:
- `GET /api/tools`
- `POST /api/tools/{tool_name}`
- This unblocks `dopecon-bridge`'s legacy `POST /api/tools/{tool}` integration path.

1. Health and discovery hardening
- `GET /health` now returns structured JSON.
- `GET /health?deep=1` performs live Leantime readiness check.
- `/info` now publishes endpoint URLs derived from request base URL and includes REST tool endpoint.

1. PM route execution in dopecon-bridge
- `/route/pm` now maps supported `leantime.*` operations to real leantime-bridge tool calls instead of mock-only behavior.
- Response normalization preserves client expectations (`tasks`, `task_id`, `project_id`).
- `/route/leantime` now reuses the same PM execution path.

1. Status sync tool correction
- Updated task status sync to call `update_ticket` (existing tool) instead of non-existent `update_ticket_status`.

1. Canonical compose integration
- Root `compose.yml` now includes `mysql_leantime`, `redis_leantime`, and `leantime` services.
- `task-orchestrator` and `leantime-bridge` now depend on `leantime` in canonical stack startup.

1. Runtime path convergence
- `services/dopecon-bridge/Dockerfile` now runs `python -m dopecon_bridge.app`.
- `dopecon_bridge.app` now delegates to `main.py` app to ensure a single runtime implementation.

1. Contract tests added
- Added PM route + tool endpoint contract tests:
- `services/dopecon-bridge/tests/test_leantime_route_contract.py`
- `docker/mcp-servers/leantime-bridge/test_contract_api_tools.py`

## Remaining Gaps to Reach Production Grade

### Critical

1. Deployment profile hardening
- Canonical compose now includes LeanTime stack, but production profile still needs:
- resource limits
- secrets management strategy
- backup/restore wiring for Leantime volumes

1. End-to-end failure path tests
- Baseline contract tests exist, but still needed:
- retry/backoff behavior under upstream failures
- auth failure coverage (invalid API token)
- timeout and partial outage cases

### High

1. Plugin implementation alignment
- Leantime plugin tree has duplicate locations and mixed conventions.
- Some plugin code paths look framework-mismatched and need canonicalization and runtime verification.

1. Operation semantics coverage
- `allocate_resource` and `update_sprint` currently map to best-effort ticket updates.
- Needs explicit domain model and contract-level mapping to Leantime-native objects.

1. Security hardening
- Enforce auth strategy for `/api/tools/*` in containerized deployments.
- Define token scopes and ingress policy between services.

### Medium

1. Observability
- Add PM-specific metrics and dashboards:
- operation latency and error rate by tool
- method-fallback hit rate
- route/pm success/failure ratio

1. Data reconciliation
- Add scheduled drift detection between Dopemux task IDs and Leantime ticket IDs.

## Production Completion Plan

1. Deployment convergence
- Create canonical compose profile including Leantime stack and explicit inter-service dependencies.

1. Contract and E2E testing
- Add integration tests for PM routing and bridge tool execution with real Leantime test fixture.

1. Runtime cleanup
- Consolidate dopecon-bridge entrypoint and remove dead/mock route paths.

1. Plugin cleanup
- Canonicalize one plugin tree, remove duplicates, verify lifecycle hooks in real Leantime runtime.

1. Security and SLOs
- Add auth on bridge REST tool endpoint, observability, alert thresholds, and runbooks.
