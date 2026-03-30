# Implementation Plan: TP-SIA-EXEC-0001 (Deterministic Execution Lease Core)

## 1. Objective
Replace the current execution-plane lease core with a fail-closed model that can survive contention, expiry, stale agents, duplicate release calls, and operator overrides. The old `READY/LEASED/EXECUTING/PROOF_GENERATED/AUDITED/COMMITTED` model and `checkout/heartbeat/release` API are superseded by a stricter packet state machine, fencing tokens, structured results, and auditable events.

## 2. Canonical execution model

### 2.1 Packet lifecycle
Primary execution states are:

- `PENDING`
- `LEASED`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`
- `CANCELLED`
- `ABANDONED`

Rules:

- `PENDING` is the only claimable state.
- A packet is claimable only when every dependency is `SUCCEEDED`.
- `LEASED` means checkout succeeded but execution has not yet demonstrated liveness.
- `RUNNING` begins on the first successful renew.
- `SUCCEEDED`, `FAILED`, `CANCELLED`, and `ABANDONED` are terminal.
- Proof, audit, and commit milestones are no longer packet states; they remain metadata and result artifacts.

### 2.2 Packet data
`ExecutionPacket` must carry at least:

- `packet_id`, `owner_id`, optional `task_id`
- `depends_on`, `state`
- `attempt_count`, `max_attempts`
- `last_error`, `last_agent_id`
- `current_fencing_token`
- `priority`, `routing_hints`
- `canonical_inputs`, `expected_outputs`, `proof_requirements`
- `metadata`, `proof_bundle`
- `created_at_utc`, `updated_at_utc`

### 2.3 Lease data
`PacketLease` must carry at least:

- `lease_id`, `packet_id`
- `agent_id`, `worker_instance_id`
- `fencing_token`
- `issued_at_utc`, `expires_at_utc`, `last_renewed_at_utc`
- `ttl_seconds`
- `state` in `ACTIVE`, `EXPIRED`, `RELEASED`, `REVOKED`

### 2.4 Result and event data
`ExecutionResult` records:

- `result_id`, `packet_id`, `lease_id`
- `disposition`
- `summary`, `payload`, `error_code`, `proof_ref`
- `completed_at_utc`

`ExecutionEvent` records:

- `event_id`, `event_type`
- `packet_id`, optional `lease_id`
- optional `fencing_token`
- `actor_id`, optional `worker_instance_id`
- `occurred_at_utc`
- `details`

## 3. Canonical store surface

### 3.1 ExecutionStore ownership
`ExecutionStore` owns persistence for:

- packets
- results
- events

### 3.2 LeaseStore ownership
`LeaseStore` owns:

- exclusive checkout
- renew semantics
- release semantics
- expiry and reassignment
- cancellation and revocation
- operator status inspection

### 3.3 Required API
The canonical in-memory surface is:

- `checkout_packet(agent_id, worker_instance_id, packet_id=None, queue=None, capabilities=None, routing_hints=None, ttl_seconds=300)`
- `renew_lease(lease_id, agent_id, worker_instance_id, fencing_token)`
- `release_lease(lease_id, agent_id, worker_instance_id, fencing_token, disposition, result)`
- `cancel_packet(packet_id, reason, actor, force=True)`
- `get_packet_status(packet_id)`
- `expire_leases(now=None)`

## 4. Required semantics

### 4.1 Checkout
On every successful checkout:

- the packet fencing token increments
- the packet attempt count increments
- the packet transitions to `LEASED`
- an active lease is created
- `LEASE_ACQUIRED` is emitted

Queue-based selection is deterministic:

- `priority` descending
- `created_at_utc` ascending
- `packet_id` ascending

### 4.2 Renew
A renew succeeds only when:

- the lease exists
- the lease is `ACTIVE`
- the agent and worker instance match
- the supplied fencing token matches the lease token
- the supplied fencing token still matches the packet token
- current time is before `expires_at_utc`

On the first successful renew, the packet transitions from `LEASED` to `RUNNING`.

### 4.3 Release
A release succeeds only when the lease is still active and the caller owns the current fencing token.

Successful release must:

- persist an `ExecutionResult`
- transition the packet to the terminal state implied by the disposition
- clear the active lease
- emit `RESULT_RECORDED` and `LEASE_RELEASED`

Duplicate release is idempotent only when the stored final result matches exactly. Conflicting duplicate release calls fail.

### 4.4 Expiry
Expiry is authoritative at `expires_at_utc`. It may be observed during renew or release or applied by `expire_leases()`.

When a lease expires:

- the lease transitions to `EXPIRED`
- stale renew and release calls fail
- the packet transitions to `PENDING` while `attempt_count < max_attempts`
- the packet transitions to `ABANDONED` once `attempt_count >= max_attempts`
- structured expiry and requeue or abandon events are emitted

### 4.5 Cancellation
`cancel_packet()` is the operator override path.

When force-cancel is applied to an active lease:

- the lease becomes `REVOKED`
- the packet becomes `CANCELLED`
- later renew and release calls fail
- structured revocation and cancellation events are emitted

## 5. Rollout boundaries
This packet stops at the in-memory execution core.

Explicitly deferred:

- Redis-backed leasing
- distributed compare-and-set
- dead-letter queues and poison-packet handling beyond `ABANDONED`
- TaskDecomposer or scheduler wiring
- richer routing policy beyond deterministic queue, dependency, and capability filtering

## 6. Verification strategy
The minimum proving set is:

- packet creation and initial event emission
- targeted checkout with fencing token and attempt increment
- deterministic queue checkout with dependency, queue, and capability filtering
- double checkout rejection
- renew ownership and stale-token rejection
- release result persistence and duplicate-release idempotency
- stale release rejection after expiry and reassignment
- expiry requeue and abandon behavior by retry budget
- operator cancellation and revocation behavior
- result persistence failure without false success
- contention test proving only one concurrent checkout wins
- renew versus sweeper race behavior
- status inspection returning packet, lease, result, and events
