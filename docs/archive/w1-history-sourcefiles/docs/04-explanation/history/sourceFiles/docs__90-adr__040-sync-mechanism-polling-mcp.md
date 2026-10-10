# ADR-040: Sync Mechanism = Polling MCP/JSON-RPC Loop

**Status:** Proposed
**Date:** 2025-09-25
**Context:** Zero-Touch Sync across Leantime, Task-Master, and ConPort

## Context

We need a synchronization mechanism to keep data consistent across Leantime, Task-Master, and ConPort. Options include:
- Event-driven webhooks/message queues
- Polling-based sync loops
- Hybrid approaches with eventual consistency

The chosen approach affects complexity, reliability, and time-to-implementation.

## Decision

Implement a **polling-based sync loop** (default 300s interval) using MCP and JSON-RPC interfaces, with retries and backoff for reliability.

## Rationale

- **Fast rollout**: No additional infrastructure required (no message queues, webhook endpoints)
- **Simplicity**: Single process handles all sync logic with predictable behavior
- **Existing interfaces**: All systems already expose MCP/JSON-RPC interfaces
- **Reliability**: Polling is more resilient to temporary network issues than webhooks
- **Debuggability**: Easy to trace sync operations and replay failed syncs
- **Evolution path**: Can migrate to event-driven later without changing data contracts

## Consequences

### Positive
- Rapid implementation and deployment
- No additional infrastructure dependencies
- Simple operational model (one process, configurable interval)
- Easy to debug and monitor sync operations
- Graceful handling of system downtime (retries with backoff)

### Negative
- Slight delay in sync (up to interval duration)
- Potential for unnecessary polling when no changes occur
- Higher resource usage than pure event-driven approach

### Neutral
- Default 300s interval balances responsiveness with efficiency
- Can be tuned per-environment (faster for dev, slower for production)
- Will evolve to event-driven webhooks in future iterations

## Implementation

1. Single sync service polls each system via MCP/JSON-RPC every 300s
2. Exponential backoff with jitter for retries on failures
3. Dead-letter queue for persistent sync failures requiring manual review
4. Health checks for each system endpoint before sync attempts
5. Configurable intervals and feature flags for gradual rollout

## Metrics & Monitoring

- `sync_pass_duration_ms`: Time to complete full sync cycle
- `sync_writes_success_total`: Successful write operations
- `sync_writes_error_total`: Failed write operations by system
- `sync_conflicts_total`: Number of conflicts requiring manual review
- `review_queue_length`: Backlog of items needing manual attention

## References

- [RFC: Zero-Touch Sync](../01-decisions/RFC-zero-touch-sync.md)
- [ADR-041: Conflict Resolution](./041-conflict-resolution-lww-precedence.md)
- [Runbook: Zero-Touch Sync Operations](../92-runbooks/runbook-zero-touch-sync.md)