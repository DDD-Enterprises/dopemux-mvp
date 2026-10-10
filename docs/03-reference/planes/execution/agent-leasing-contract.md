---
id: execution-agent-leasing-contract
title: Agent Leasing Contract
type: reference
owner: '@codex'
last_review: '2026-03-26'
next_review: '2026-04-26'
author: '@codex'
date: '2026-03-26'
prelude: Canonical execution-plane lease rules for packet checkout, renewal, release, expiry, and cancellation.
---
# Agent Leasing Contract

## Overview
The execution plane is fail-closed. No agent may execute packet work without an `ACTIVE` lease, and lease ownership is enforced by `lease_id`, `agent_id`, `worker_instance_id`, and `fencing_token` together.

## Canonical packet lifecycle
The execution core uses exactly these packet states:

- `PENDING`
- `LEASED`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`
- `CANCELLED`
- `ABANDONED`

`PENDING` is the only claimable state. A packet is claimable only when all dependencies are in `SUCCEEDED`.

Proof, audit, and commit milestones are not execution states. They remain secondary metadata or result artifacts.

## Canonical lease API
Agents and control-plane callers must use the execution store surface below:

- `checkout_packet(agent_id, worker_instance_id, packet_id=None, queue=None, capabilities=None, routing_hints=None, ttl_seconds=300)`
- `renew_lease(lease_id, agent_id, worker_instance_id, fencing_token)`
- `release_lease(lease_id, agent_id, worker_instance_id, fencing_token, disposition, result)`
- `cancel_packet(packet_id, reason, actor, force=True)`
- `get_packet_status(packet_id)`
- `expire_leases(now=None)`

`checkout_packet()` supports both targeted claims and queue-based claims. Queue selection is deterministic: `priority` descending, then `created_at_utc` ascending, then `packet_id` ascending.

## Lease ownership and fencing
Every successful checkout increments the packet fencing token and the packet attempt count.

A lease remains valid only while all of the following are true:

- lease state is `ACTIVE`
- caller `agent_id` matches the lease owner
- caller `worker_instance_id` matches the lease owner
- supplied `fencing_token` matches the lease token
- supplied `fencing_token` still matches the packet's current fencing token
- current time is before `expires_at_utc`

Stale renew or release calls are rejected. Heartbeat expiry alone is not sufficient protection; the fencing token is the stale-writer guard.

## Renewal semantics
Default TTL is `300` seconds. Recommended renew cadence is `60` seconds. There is no grace window.

`renew_lease()` is allowed repeatedly while the lease is active. On the first successful renew, a packet transitions from `LEASED` to `RUNNING`. Later renews keep the lease active and extend `expires_at_utc` by the lease TTL.

If a lease has expired, been revoked, or been replaced by a newer lease, renew fails.

## Release semantics
`release_lease()` requires a structured result payload and a final disposition.

Valid dispositions are:

- `SUCCEEDED`
- `FAILED`
- `CANCELLED`
- `ABANDONED`

A successful release persists an `ExecutionResult`, clears the active lease, and transitions the packet to the terminal state implied by the supplied disposition.

Duplicate release is idempotent only when the stored result exactly matches the incoming result payload. Conflicting duplicate releases fail deterministically.

## Expiry and retry semantics
Expiry is authoritative at `expires_at_utc`. It may be detected passively during renew or release or actively via `expire_leases()`; both paths must produce the same result.

When an active lease expires:

- the lease transitions to `EXPIRED`
- stale renew and release calls fail
- the packet transitions to `PENDING` when `attempt_count < max_attempts`
- the packet transitions to `ABANDONED` when `attempt_count >= max_attempts`

The first in-memory implementation only auto-retries lease-expiry cases. Explicit `FAILED` releases remain terminal.

## Cancellation and operator override
`cancel_packet()` is the operator override path. When force-cancel is used against an active lease:

- the lease becomes `REVOKED`
- the packet becomes `CANCELLED`
- later renew and release calls for that lease fail

## Required audit events
Execution transitions must emit structured events. The first implementation records these in-memory:

- `PACKET_CREATED`
- `LEASE_ACQUIRED`
- `LEASE_RENEWED`
- `LEASE_EXPIRED`
- `LEASE_RELEASED`
- `LEASE_REVOKED`
- `RESULT_RECORDED`
- `PACKET_REQUEUED`
- `PACKET_CANCELLED`
- `PACKET_ABANDONED`

`get_packet_status()` is the minimum operator-facing inspection surface. It must expose the packet, current active or last lease, latest result if any, and the recent event trail needed to explain current state.

## Follow-on work
This contract intentionally stops at the in-memory implementation and invariant proof.

Out of scope for this packet:

- Redis-backed lease storage
- distributed compare-and-set
- dead-letter queues
- richer scheduling policy beyond deterministic queue selection
- TaskDecomposer or CLI wiring beyond future integration points
