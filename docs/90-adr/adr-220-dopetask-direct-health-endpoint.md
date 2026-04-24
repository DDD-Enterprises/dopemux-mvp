---
id: adr-220
title: dopetask Direct Health Endpoint
type: adr
owner: Claude Agent
date: 2026-04-23
status: active
prelude: "dopetask exposes a direct /health endpoint so the Services pane can probe it without relying on a central aggregator."
tags: [u2-resolved, services-health, dopetask, execution-plane, monitoring]
adhd_summary: "Direct health probe from Services pane, no aggregation bottleneck"
graph_metadata: {}
---

# ADR-220: dopetask Direct Health Endpoint

## Summary

dopetask exposes a direct `/health` endpoint that Services pane probes directly, rather than routing health checks through a central aggregator.

## Problem

Health monitoring in the execution plane requires real-time visibility into dopetask state. A centralized health rollup endpoint creates a cascading failure problem:
- If dopetask is down, the aggregator cannot reach it
- The entire health report becomes unreliable
- Services pane loses execution plane visibility precisely when it's needed most

## Solution

dopetask exposes its own health directly via `GET /health` endpoint. Services pane probes dopetask directly every 5 seconds, avoiding intermediate dependencies.

### Endpoint Specification

**Route**: `GET /health`

**Response Format**:
```json
{
  "status": "healthy|degraded|critical",
  "uptime": 3600,
  "workers_active": 12,
  "timestamp": "2026-04-23T14:30:00Z"
}
```

**HTTP Status Codes**:
- `200`: Healthy (status='healthy')
- `503`: Degraded (status='degraded')
- `500`: Critical failure (status='critical')

**Performance Requirements**:
- Response time < 50ms
- No external dependencies (in-memory state only)
- No database queries
- No I/O operations

### Monitoring

**Probe Cadence**: Every 5 seconds from Services pane

**Monitored Metrics**:
- uptime: Worker process uptime in seconds
- workers_active: Number of active worker threads
- status: Current operational state

**Alerting**:
- Status change to 'degraded': Warning alert
- Status change to 'critical': Critical alert
- Probe timeout (> 5 seconds): Probe failure alert

## Rationale

1. **Execution-Critical Service**: dopetask failures are system-critical; delays in detection cascade to dependent services
2. **Failure Independence**: Direct endpoint ensures health visibility even when intermediate services fail
3. **Real-Time Visibility**: Sub-5-second latency enables PLAN/ACT pane to respond immediately to dopetask state changes
4. **Monitoring Simplicity**: Single-responsibility endpoint (health only), no rollup logic coupling

## Consequences

### Positive
- Services pane can detect dopetask failures immediately (< 5 seconds)
- No cascading failures from aggregation bottlenecks
- Clear operational responsibility: dopetask owns its health reporting
- Independent probe circuit enables fault isolation testing

### Negative
- Services pane must probe all services individually (vs. centralized health)
- More network round-trips required at scale
- Health state changes are not atomic across all services

### Mitigations
- Probe responses cached by Services pane (configurable TTL)
- Failed probes retried with exponential backoff
- Circuit breaker on persistent failure (fallback to degraded assumption)

## Cross-References

- **Specification**: `spec/§12-Services-Pane` - Services health monitoring detailed design
- **Related ADR**: ADR-221 (Event Stream Rate Limits) - health_changed events subject to backpressure
- **Implementation Docs**: `docs/03-reference/systems/dopemux/services-pane.md`
- **Linked Questions**: TUI-unknown-resolution-questionnaire.md (U2 row)

## Implementation Status

**Resolved** - Direct health endpoint chosen over aggregated rollup

**Code Locations**:
- `services/dopetask/health.py` - Health endpoint implementation
- `services/pane/services.py` - Services pane health probe logic
- `tests/integration/test_health_monitoring.py` - Health probe test suite

## Acceptance Criteria

- [x] Direct `/health` endpoint responds in < 50ms
- [x] Services pane successfully probes dopetask every 5 seconds
- [x] Health status changes trigger Services pane UI updates
- [x] Failed probes do not block UI updates
- [x] Integration tests validate health endpoint reliability
