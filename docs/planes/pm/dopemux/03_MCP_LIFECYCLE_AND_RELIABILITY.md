---
id: 03_MCP_LIFECYCLE_AND_RELIABILITY
title: MCP Lifecycle and Reliability
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-15'
last_review: '2026-02-15'
next_review: '2026-05-16'
prelude: MCP Lifecycle and Reliability (explanation) for dopemux documentation and developer
  workflows.
plane: pm
component: dopemux
status: proposed
---

# MCP Lifecycle and Circuit Breakers

## Purpose
How MCP servers start, fail, recover, and how the system degrades gracefully. This document defines the resilience layer for tool integration.

## Scope
* Startup/Shutdown orchestration of MCP servers.
* Health monitoring and heartbeats.
* Automatic restart policies.
* Fallback routing when tools fail.
* Classification of servers as Required vs Optional.

---

## Non-negotiable invariants

### INV-MCP-001: No Zombie Processes

**INV-ID**: INV-MCP-001
**Statement**: When Dopemux exits (cleanly or via signal), ALL child MCP server processes MUST be terminated. No orphaned server processes may persist.
**Scope**: system-wide
**Owner**: Supervisor (process manager)
**Enforcement Surface**:
* Docker Compose `restart: unless-stopped` policy — containers restart only if not explicitly stopped.
* `docker compose down` sends SIGTERM to all services, then SIGKILL after timeout.
* Process group management if running outside Docker.
**Violation Mode**: Resource leak — orphaned MCP servers consume ports, memory, and database connections.
**Detection Method**:
* After `docker compose down`: `docker ps --filter name=dopemux` must return zero running containers.
* Port scan: ports 3003-3016 must be free after shutdown.
**Recovery Strategy**: `docker compose down --remove-orphans`. If processes persist: `docker kill $(docker ps -q --filter name=dopemux)`.
**Evidence**:
* `compose.yml`: All services use `restart: unless-stopped` (not `always`), meaning explicit `docker compose down` stops them permanently.
* Docker Compose lifecycle: `down` sends SIGTERM → grace period → SIGKILL.

---

### INV-MCP-002: Fail-Safe on Required Server Down

**INV-ID**: INV-MCP-002
**Statement**: If a REQUIRED MCP server is down, operations dependent on it MUST fail explicitly with a clear error message. They MUST NOT hang, return stale data, or silently degrade.
**Scope**: per-request
**Owner**: Supervisor (routing layer)
**Enforcement Surface**:
* Docker Compose `depends_on` with `condition: service_healthy` for critical dependencies.
* Runtime health checks before routing requests.
* Timeout enforcement on all MCP calls (no infinite waits).
**Violation Mode**: Silent failure — system appears functional but produces incorrect results because a critical server is absent.
**Detection Method**:
* Health endpoint returns non-healthy status.
* Request to required server times out or returns connection refused.
* Supervisor logs: `"Cannot execute: [server] is unavailable and required for this task."`.
**Recovery Strategy**: Surface clear error to operator. Do not retry indefinitely — fail after configured retry count.
**Evidence**:
* `compose.yml`: `task-orchestrator` depends on `redis-primary` (healthy) and `conport`. `conport` depends on `postgres` (healthy) and `redis-primary` (healthy).
* `adhd-engine` depends on `redis-primary` (healthy).

---

### INV-MCP-003: Circuit Breaking on Repeated Failure

**INV-ID**: INV-MCP-003
**Statement**: A failing MCP server MUST be isolated after repeated failures to prevent system-wide latency degradation. The circuit breaker transitions: CLOSED -> OPEN (after N failures) -> HALF-OPEN (after cooldown) -> CLOSED (on success).
**Scope**: per-server
**Owner**: MCPServerManager
**Enforcement Surface**:
* Circuit breaker state machine per MCP server.
* Failure counter with configurable threshold.
* Cooldown timer before HALF-OPEN probe.
**Violation Mode**: Cascade failure — one slow/broken server drags down all requests that touch it.
**Detection Method**:
* Failure counter exceeds threshold (default: 3 consecutive failures).
* P95 latency exceeds threshold (configurable per-server).
* Server marked UNHEALTHY in routing table.
**Recovery Strategy**:
* OPEN state: all requests to this server fail-fast (no actual call made).
* After cooldown (default: 30s): transition to HALF-OPEN, send one probe request.
* If probe succeeds: transition to CLOSED (normal).
* If probe fails: back to OPEN, reset cooldown timer.
**Evidence**:
* FUTURE: Circuit breaker implementation. Current system relies on Docker Compose `restart: unless-stopped` for basic recovery.
* Design requirement in this document.

---

### INV-MCP-004: Startup Dependency Order

**INV-ID**: INV-MCP-004
**Statement**: MCP servers MUST start in dependency order. Infrastructure (PostgreSQL, Redis, Qdrant) MUST be healthy before application services (ConPort, task-orchestrator) attempt to connect.
**Scope**: system startup
**Owner**: Docker Compose / Supervisor
**Enforcement Surface**:
* `compose.yml` `depends_on` with `condition: service_healthy` enforces ordering.
* `start_period` in healthchecks gives services time to initialize before declaring unhealthy.
**Violation Mode**: Connection errors, crash loops — service starts before its dependency is ready.
**Detection Method**:
* Container enters restart loop (visible in `docker compose ps`).
* Logs show connection refused or database not ready errors.
**Recovery Strategy**: Docker Compose automatically retries based on `restart: unless-stopped`. Services with `start_period` get grace time.
**Evidence**:
* `compose.yml` dependency chain:
  * `postgres` → healthcheck `pg_isready`, `start_period: 20s`
  * `redis-events` → healthcheck `redis-cli ping`
  * `redis-primary` → healthcheck `redis-cli ping`
  * `conport` → depends on `postgres`, `redis-primary`, `mcp-qdrant`, `dopecon-bridge`
  * `task-orchestrator` → depends on `redis-primary`, `conport`, `leantime`
  * `adhd-engine` → depends on `redis-primary`
  * `dopecon-bridge` → depends on `postgres` (healthy), `redis-events` (healthy), `mcp-qdrant` (started)

---

### INV-MCP-005: Required vs Optional Server Classification

**INV-ID**: INV-MCP-005
**Statement**: Every MCP server MUST be classified as REQUIRED or OPTIONAL. Operations MUST refuse if a REQUIRED server is unavailable. Operations SHOULD degrade gracefully if an OPTIONAL server is unavailable.
**Scope**: system configuration
**Owner**: Architecture (PM plane)

**Classification (derived from compose.yml evidence)**:

| Server | Port | Classification | Rationale |
|--------|------|----------------|-----------|
| postgres (AGE) | 5432 | REQUIRED | Backing store for ConPort, LiteLLM. Everything depends on it. |
| redis-events | 6379 | REQUIRED | EventBus streaming. DopeconBridge depends on it (healthy). |
| redis-primary | — | REQUIRED | Caching. ConPort, task-orchestrator, adhd-engine depend on it (healthy). |
| conport | 3004 | REQUIRED | Knowledge graph authority (INV-MEM-002). Multiple services depend on it. |
| dopecon-bridge | 3016 | REQUIRED | Event processing. ConPort depends on it. |
| qdrant | 6333 | REQUIRED | Vector DB for semantic search. ConPort and dope-context depend on it. |
| litellm | 4000 | OPTIONAL | Model router. Services can fall back to direct API calls. |
| pal (zen) | 3003 | OPTIONAL | Multi-model reasoning. Enhances but not required for core operations. |
| dope-context | 3010 | OPTIONAL | Semantic search. Fallback: grep/ripgrep keyword search. |
| serena | 3006 | OPTIONAL | ADHD engine interface. System functions without ADHD accommodations. |
| gptr-mcp | 3009 | OPTIONAL | Deep research. Not required for core task execution. |
| desktop-commander | 3012 | OPTIONAL | Desktop automation. No core dependency. |
| leantime-bridge | 3015 | OPTIONAL | PM integration. Task-orchestrator degrades without it. |
| leantime | 8080 | OPTIONAL | PM UI. System functions without web PM interface. |

**Enforcement Surface**:
* Startup: REQUIRED servers use `condition: service_healthy` in `depends_on`.
* Runtime: routing layer checks classification before deciding fail vs degrade.
**Violation Mode**: System runs in degraded state without operator awareness.
**Detection Method**: Health dashboard showing REQUIRED server as unhealthy triggers alert.
**Recovery Strategy**: REQUIRED server down → halt dependent operations. OPTIONAL server down → log warning, use fallback.
**Evidence**:
* `compose.yml` dependency analysis (lines 248-404): healthy conditions used for postgres, redis-events, redis-primary. Started conditions for qdrant.

---

### INV-MCP-006: Health Monitoring Contract

**INV-ID**: INV-MCP-006
**Statement**: Every MCP server MUST expose a `/health` endpoint. The health response MUST indicate service status. Health checks MUST run at the intervals specified in compose configuration.
**Scope**: per-server
**Owner**: Each MCP server
**Enforcement Surface**:
* `compose.yml` healthcheck definitions for every service.
* Standardized health endpoint returning status.
**Violation Mode**: Undetected failure — server is down but system doesn't know.
**Detection Method**:
* Healthcheck failure triggers Docker to mark container as unhealthy.
* Dependent services that require `service_healthy` will not start or will notice the change.
**Recovery Strategy**: `restart: unless-stopped` triggers automatic container restart on failure.
**Evidence**:
* All services in `compose.yml` have `healthcheck` blocks:
  * `postgres`: `pg_isready`, interval 10s, retries 10, start_period 20s.
  * `redis-*`: `redis-cli ping`, interval 10s, retries 3.
  * `conport`: `curl -f http://localhost:3004/health`, interval 30s, retries 3, start_period 30s.
  * `dopecon-bridge`: `curl -f http://localhost:3016/health`, interval 30s, retries 3, start_period 30s.
  * `task-orchestrator`: `curl -f http://localhost:8000/health`, interval 30s, retries 3, start_period 40s.
  * `adhd-engine`: `curl -f http://localhost:8095/health`, interval 30s, retries 3, start_period 30s.
  * `pal`: `exit 0` (always healthy — no real check). **GAP**: should have real health endpoint.
  * `dope-context`: `curl -f http://localhost:3010/health  exit 0`. **GAP**: `exit 0` fallback means unhealthy is never reported.
  * `conport`: `curl -f http://localhost:3004/health  exit 0`. **GAP**: same `exit 0` fallback issue.

**GAPS IDENTIFIED**:
* `pal` healthcheck is `exit 0` — always passes regardless of actual health.
* `conport` and `dope-context` use `exit 0` — failures are swallowed.
* These should be fixed to return real health status.

---

## FACT ANCHORS (Repo-derived)

* **OBSERVED: Canonical Compose**: `compose.yml` at repo root (628 lines). Defines all services.
* **OBSERVED: Infrastructure**: PostgreSQL AGE (`apache/age:release_PG16_1.6.0`), Redis 7-alpine (2 instances: events + primary), Qdrant latest.
* **OBSERVED: MCP Servers**: ConPort (3004), PAL/Zen (3003), LiteLLM (4000), Dope-Context (3010), Serena (3006), GPTR (3009), Desktop Commander (3012), Leantime Bridge (3015).
* **OBSERVED: Application Services**: DopeconBridge (3016), Task Orchestrator (8000), ADHD Engine (8095), Genetic Agent (8000), Dope-Memory (3020/8096).
* **OBSERVED: Dependency Chain**: postgres → conport → task-orchestrator; redis-events → dopecon-bridge → conport.
* **OBSERVED: Health Endpoints**: All services have healthcheck blocks in compose.yml, but quality varies (some use `exit 0` fallback).
* **OBSERVED: Task-Orchestrator Tools**: `/info` endpoint reports "37 tools" (line 306 of main.py).
* **OBSERVED: Restart Policy**: All services use `restart: unless-stopped`.

---

## Failure modes

### 1. Infrastructure Cascade
* **Trigger**: PostgreSQL crashes.
* **Impact**: ConPort, LiteLLM, DopeconBridge all lose their backing store. Cascade failure across REQUIRED services.
* **Severity**: S0 critical.
* **Containment**: PostgreSQL has `restart: unless-stopped` and healthcheck with 10 retries. Dependent services wait for healthy condition.
* **Gap**: No alerting mechanism defined for cascade detection.

### 2. Redis Split-Brain
* **Trigger**: Two Redis instances (events + primary) used for different purposes. One goes down.
* **Impact**: If `redis-events` fails: DopeconBridge loses event streaming. If `redis-primary` fails: ConPort, task-orchestrator, adhd-engine lose caching.
* **Severity**: S1 high (redis-events), S2 medium (redis-primary — caching is not authority).
* **Containment**: Healthchecks detect within 30s. `restart: unless-stopped` auto-recovers.

### 3. Port Conflict
* **Trigger**: Multiple services bind to same port (e.g., task-orchestrator and genetic-agent both on 8000).
* **Impact**: One service fails to start.
* **Severity**: S1 high.
* **Evidence**: `compose.yml` shows `genetic-agent` exposes `8000:8000` and `task-orchestrator` does NOT expose ports (relies on internal networking). But if both containers try to bind host port 8000, conflict occurs.
* **Containment**: Docker Compose will error on startup if host ports conflict.

### 4. Swallowed Health Failures
* **Trigger**: Services using `exit 0` in healthcheck (conport, dope-context, pal).
* **Impact**: Docker reports container as healthy when it may not be. Dependent services start prematurely or don't detect failures.
* **Severity**: S2 medium.
* **Containment**: Fix healthchecks to remove `exit 0` fallback. Replace `exit 0` in pal with actual health probe.

### 5. Startup Race Condition
* **Trigger**: `depends_on` with `condition: service_started` (not `service_healthy`) — used for `mcp-qdrant` in dopecon-bridge.
* **Impact**: DopeconBridge may attempt to connect to Qdrant before it's ready.
* **Severity**: S2 medium.
* **Containment**: Qdrant typically starts fast. Application-level retry handles transient connection failure.

---

## Enforcement surface summary

| Invariant | Enforcement Point | Mechanism | Automated? |
|-----------|-------------------|-----------|------------|
| INV-MCP-001 | Docker Compose | `down` sends SIGTERM/SIGKILL | Yes |
| INV-MCP-002 | `depends_on` | `condition: service_healthy` | Yes (for startup) |
| INV-MCP-002 | Runtime | Timeout + explicit error | FUTURE |
| INV-MCP-003 | MCPServerManager | Circuit breaker state machine | FUTURE |
| INV-MCP-004 | Docker Compose | `depends_on` + `start_period` | Yes |
| INV-MCP-005 | Configuration | Classification table (this doc) | Documentation only |
| INV-MCP-006 | Docker Compose | `healthcheck` blocks | Yes (with gaps noted) |

---

## Degradation ladder

| Level | Condition | Behavior | User Impact |
|-------|-----------|----------|-------------|
| L0: Nominal | All servers healthy | Full capability | None |
| L1: Optional Degraded | One or more OPTIONAL servers down | Reduced capability with fallbacks | Slower search, no desktop automation, etc. |
| L2: Cache Lost | Redis-primary down | Continue without caching | Slower response times |
| L3: Event Bus Down | Redis-events down | DopeconBridge degraded | No real-time event streaming |
| L4: Authority Degraded | ConPort slow (>5s response) | Queue writes, warn operator | Decision recording delayed |
| L5: Authority Down | ConPort unreachable | Refuse authority operations | Cannot make formal decisions |
| L6: Infrastructure Down | PostgreSQL down | All REQUIRED services fail | Full stop |

---

## Determinism guarantees

* **Startup Order**: Deterministic given Docker Compose dependency graph and healthchecks.
* **Health Check Timing**: Determined by `interval`, `timeout`, `retries`, `start_period` in compose.yml.
* **Restart Behavior**: `unless-stopped` policy is deterministic — restart on crash, don't restart after explicit stop.
* **Non-deterministic**: Exact timing of service readiness after restart (depends on system load, DB recovery time, etc.).

---

## Contradiction analysis

| Claim | Source | Status |
|-------|--------|--------|
| ConPort uses `exit 0` healthcheck | compose.yml line 254 | CONFIRMED — masks failures |
| PAL healthcheck is `exit 0` | compose.yml line 277 | CONFIRMED — never actually checks health |
| Dope-context uses `exit 0` | compose.yml line 334 | CONFIRMED — masks failures |
| Task-orchestrator has real health | compose.yml line 406 | CONFIRMED — `curl -f` without fallback |
| DopeconBridge has real health | compose.yml line 372 | CONFIRMED — `curl -f` without fallback |
| `config/mcp_servers.yaml` exists | Earlier doc version | NOT FOUND — file does not exist in repo |
| `src/dopemux/mcp/manager.py` exists | Earlier doc version | NOT VERIFIED — needs confirmation |
| All servers expose `/health` | Design requirement | PARTIALLY — pal has no real health endpoint |

---

## MCPServerManager responsibilities

* **Startup**: Launch servers in dependency order (enforced by Docker Compose).
* **Health**: Monitor via Docker healthchecks + application-level probes.
* **Routing**: Maintain a map of `Tool Name -> Server ID` with health status.
* **Recovery**: Docker's `restart: unless-stopped` handles basic recovery. Circuit breaker (FUTURE) handles repeated failure.

## Startup order (from compose.yml dependency graph)

```
Layer 0 (Infrastructure):
  postgres       — healthcheck: pg_isready, start_period: 20s
  redis-events   — healthcheck: redis-cli ping
  redis-primary  — healthcheck: redis-cli ping
  mcp-qdrant     — no healthcheck (started only)

Layer 1 (Event Processing):
  dopecon-bridge — depends: postgres(healthy), redis-events(healthy), mcp-qdrant(started)

Layer 2 (Core MCP):
  conport        — depends: postgres, redis-primary, mcp-qdrant, dopecon-bridge
  dope-context   — depends: mcp-qdrant

Layer 3 (Application):
  task-orchestrator — depends: redis-primary, conport, leantime
  adhd-engine       — depends: redis-primary
  genetic-agent     — depends: pal, conport
  dope-memory       — depends: postgres(healthy), redis-events(healthy)

Layer 4 (Optional/Independent):
  pal             — no dependencies
  litellm         — depends: postgres
  serena          — no dependencies
  gptr-mcp        — no dependencies
  desktop-commander — no dependencies
  leantime-bridge — depends: mcp-qdrant, leantime
  leantime        — depends: mysql_leantime(healthy), redis_leantime(started)
```

## Circuit breaker triggers
* **Unreachable**: Connection refused > 3 times.
* **Latency**: P95 response time > 5000ms over 1 minute.
* **Error Rate**: > 20% JSON-RPC errors in a sliding window.
* **Broken Pipe**: Process crash detected by Docker healthcheck.

**Action**: State transitions to OPEN. Supervisor stops routing requests to this server. After cooldown, probe with single request (HALF-OPEN).

## Degradation and fallback behavior
If a server is UNHEALTHY or STOPPED:

1. **Tool Substitution**:
   * IF `dope-context` (Semantic Search) is down: Fall back to `grep`/`ripgrep` keyword search.
   * IF `pal` (Zen reasoning) is down: Use native Claude reasoning (no multi-model validation).
   * IF `litellm` (Model Router) is down: Direct API calls to model providers.
   * IF `leantime-bridge` is down: Task-orchestrator operates without PM sync.

1. **Refusal**:
   * If ConPort is required for an operation and is down: **STOP** and Refuse.
   * If PostgreSQL is down: **STOP** — no REQUIRED service can function.
   * Message format: `"Cannot execute: [server] is unavailable and required for this task."`

## Open questions
* **Dynamic Discovery**: Can we auto-discover new MCP servers?
  * *Resolution*: No. Usage must be explicit in compose.yml for security and determinism.
* **config/mcp_servers.yaml**: Referenced in earlier docs but does not exist.
  * *Resolution*: Compose.yml IS the canonical server registry. No separate YAML needed.

## Acceptance criteria
1. **Kill Test**: Kill an MCP server container manually. Ensure Docker detects it and restarts within 30s.
1. **Dependency Test**: Stop PostgreSQL. Ensure ConPort fails its healthcheck. Ensure task-orchestrator does not start (or restarts and fails to connect).
1. **Fallback Test**: Stop `dope-context`. Execute a search operation. Ensure it falls back to keyword search or refuses with clear message.
1. **Zombie Test**: Run `docker compose down`. Verify zero dopemux containers running with `docker ps`.
1. **Health Gap Test**: Stop the actual ConPort process inside its container (but keep container running). Verify healthcheck reports unhealthy (currently fails due to `exit 0` — this test documents the gap).
