# Local Broker Operations

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `10_LOCAL_BROKER_OPERATIONS.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Operating posture

`PROPOSED` The first broker is supervised, single-job, local, and boring on purpose. It coordinates evidence; it does not become a miniature CI platform.

## Process identity

- Dedicated non-admin `audit-broker` OS user.
- Separate home, config, temp, log, and spool directories.
- No provider credentials.
- No GitHub write credential.
- Optional read-only GitHub verifier credential in a later phase.
- No candidate repository checkout.
- No import of the aggregate Dopemux CLI path that attempted a network fetch.

## Filesystem layout concept

```text
broker-root/
  policy/                 read-only policy and schema hashes
  inbox/                  immutable request envelopes
  replay/                 durable consumed-request records
  leases/                 single-job lease state
  work-orders/            derived, signed worker instructions
  results-pending/        untrusted raw worker outputs
  results-validated/      schema-valid normalized outputs
  sealed/                 broker-sealed result bundles
  publication-pending/    exact-head recheck required
  logs/                   append-only operational logs
  quarantine/             containment or provenance failures
```

This is a conceptual layout, not an implementation instruction.

## State transitions

| State | Entry gate | Exit |
|---|---|---|
| `RECEIVED` | Request bytes accepted | Parse or reject |
| `VERIFIED` | Schema, digest, identity, repo, PR, SHA, freshness pass | Classify |
| `CLASSIFIED` | Risk/privacy/complexity computed | Await approval |
| `AWAITING_HUMAN_APPROVAL` | Route recommendation recorded | Approved or blocked |
| `LEASED` | Durable lease acquired | Dispatch or release |
| `DISPATCHED` | Worker profile frozen and launched | Result, timeout, violation |
| `RESULT_RECEIVED` | Raw output and trace stored | Validate |
| `RESULT_VALIDATED` | Schema/provenance/policy checks pass | Seal |
| `SEALED` | Content hashes and broker seal recorded | Publish or handoff |
| `STALE_HEAD` | Current head differs | Archive, never publish |
| `QUARANTINED` | Containment, identity, or integrity failure | Operator incident review |
| `FAILED` | Typed failure | Manual recovery decision |

## One-audit-at-a-time

`PROPOSED` Enforce serialization with both:

- a durable broker lease with owner, request ID, acquisition time, heartbeat, and expiry;
- upstream GitHub concurrency when the later request workflow exists.

A simple process mutex is insufficient because it cannot safely recover from crashes or duplicate submissions.

## Preflight sequence

1. Confirm broker policy and schema hashes.
2. Verify request schema and payload digest.
3. Verify repo identity and exact head through the approved source.
4. Check expiry and replay store.
5. Compute risk, privacy, complexity, and fail-closed triggers.
6. Resolve eligible routes from the adapter registry.
7. Record recommendation and human approval.
8. Reserve cost when an API route is ever eligible.
9. Acquire lease.
10. Materialize a minimal worker instruction package.
11. Launch the approved worker profile.

## Postflight sequence

1. Capture worker exit, timeout, logs, and cleanup state.
2. Parse result using the adapter-specific normalizer.
3. Validate shared result schema.
4. Verify route, provider, model, config, and certification evidence.
5. Reconcile cost and usage where applicable.
6. Recheck current PR head.
7. Seal result and evidence hashes.
8. Release lease only after cleanup state is known.
9. Hand off to human or publication queue.

## Logging

`PROPOSED` Record:

- request and result digests;
- exact repo/PR/base/head values;
- source workflow/run identity;
- classification inputs and route decision;
- human approval reference;
- adapter, tool, version, worker image, config and policy hashes;
- network profile;
- typed failures and retries;
- cleanup and revocation actions;
- publication receipt or stale-head disposition.

Never log raw secrets or unredacted sensitive diff content beyond the approved retention policy.

## Retry policy

`PROPOSED`

- Retry only the same frozen route for explicitly transient transport failures.
- Retry count is bounded and recorded.
- Do not retry auth, policy, containment, schema, identity, privacy, or cost failures.
- Do not transform quota failure into API fallback without a fresh human decision.
- A retry does not reuse a potentially compromised worker.

## Recovery

| Failure | Recovery |
|---|---|
| Broker crash with lease | Recover from durable state, inspect worker, expire lease conservatively |
| Worker crash | Destroy or quarantine worker, preserve external logs |
| Cleanup failure | Quarantine image/profile, block new dispatch |
| Replay detected | Reject and alert |
| Head changed | Mark stale, never publish |
| Publisher unavailable | Keep sealed result in publication queue |
| Suspected credential exposure | Disable adapter, revoke credential where possible, preserve evidence |

## Operator visibility

`PROPOSED` The operator must be able to see the exact request, current state, route eligibility reasons, worker profile, result validation, residual unknowns, and publication status. Hidden automation is the enemy of this release.
