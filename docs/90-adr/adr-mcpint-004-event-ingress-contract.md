---
id: adr-mcpint-004
title: 'ADR-MCPINT-004: Authenticated /events as the Single Event Ingress'
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-16'
last_review: '2026-07-17'
next_review: '2026-10-14'
prelude: Encodes gate G2 — dopecon-bridge POST /events becomes the sole authenticated event ingress with seeded users and service tokens; capture_client is the single producer library carrying per-request identity; the direct-Redis path is deprecated and mcp-capture retired.
status: accepted
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-mcpint-001
    - adr-mcpint-002
    - adr-mcpint-003
    - adr-mcpint-005
    - adr-221
    - adr-dopecon-bridge-narrowing-to-adapter-only-role
    - adr-dope-memory-as-chronicle-memory-authority
---

# ADR-MCPINT-004: Authenticated /events as the Single Event Ingress

**Status**: Accepted
**Date**: 2026-07-16
**Accepted**: 2026-07-17 — accepted by operator with PR #1073; gate answers G1-G5 2026-07-16/17; SVCFEAT reconciliation confirmed 2026-07-17.
**Owners**: @hu3mann (program DMX-MCPINT, root `af10eefd`)

## Context

The event spine that should feed the chronicle has two doors, and the wrong one is the
only one that works:

- **The designed door is dead.** dopecon-bridge `POST /events` — the only multi-consumer
  seam in the fleet (register SVC-DOPECON-BRIDGE) — rejects everything: unauthenticated
  POST → `401 {"detail":"Not authenticated"}` against an **empty user store** (P0 claim 7,
  re-confirmed live 2026-07-16; register SPINE-EVENT-CONTRACT, status `partial`).
- **The workaround became load-bearing.** `src/dopemux/memory/capture_client.py` writes
  Redis directly; ConPort's chronicle emission rides this direct-Redis path because the
  bridge door 401s. Every producer needing Redis credentials, with identity discipline
  enforced nowhere, is the standing consequence.
- **Identity is provably contaminated.** Runtime finding **N2**: the primary dope-memory
  container carries `DOPE_MEMORY_WORKSPACE_ID=dNh_CRM` — another repository's workspace id
  — so chronicle writes from this host attribute to the wrong workspace; per-project twin
  containers (N5) make the bleed systemic. Env-default identity is disproven; whatever
  ingress is blessed must carry **per-request** workspace/instance identity
  (DMX-MEMSPINE-IDENTITY-005, SVCFIN-owned, priority raised by N2).
- **Noise drowns signal.** 24,539 heartbeat rows vs 0 curated entries at audit time
  (register SPINE-HEARTBEAT-LIMIT).
- **A second capture door exists, registered nowhere.** `mcp-capture` — a real, finished
  stdio MCP server (capture/emit, SHA256 dedup, lane-aware) — is in no catalog, config, or
  compose (register MCP-CAPTURE; placement map §3).

Stream layout today (2026-07-07 chronicle-mirror runtime proof): raw events accumulate in
`dopemux:events` (3,489 at measurement) while the named consumer stream
`activity.events.v1` sat empty until the mirror fix — two streams whose roles were never
contractually defined.

**Gate G2 was answered by the user on 2026-07-16: fix the bridge JWT and bless
`/events`.**

## Decision

### 1. One authenticated door

`dopecon-bridge POST /events` is **THE** event ingress for the fleet:

- **Seed the user store** (currently empty — the root cause of the standing 401) and
  **issue service tokens** for machine producers (hooks, ConPort emitter, adhd-engine,
  bridges). Token issuance/rotation is operator-managed; no anonymous publish path exists.
- **Identity rides the request**: every accepted event carries explicit
  `workspace_id` + `instance_id` (per-request, per DMX-MEMSPINE-IDENTITY-005's contract —
  never env defaults; the N2 contamination class becomes structurally impossible at the
  door). Events without identity are rejected (fail-closed on the write's identity).
- ConPort's chronicle emission is **rerouted** through `/events`; after the reroute, the
  **direct-Redis producer path is deprecated** — retained briefly behind a removal notice,
  then deleted. Redis credentials come out of producer configs.

### 2. One producer library

`capture_client` remains the **single producer library** — the only sanctioned way any
code publishes events:

- Transport **fail-open**: a dead or slow bridge drops the event and never blocks the
  caller (capture must not become a workflow outage vector). Identity **fail-closed**: the
  library refuses to send identity-less events.
- **Heartbeat rate-limiting lives here, at the producer** (MCPINT-FND-HYG-007): session
  heartbeats are coalesced/dropped client-side so the 24.5K-row spam class cannot recur
  regardless of consumer-side policy. (Consumer-side backpressure remains governed by
  ADR-221 — unchanged.)

### 3. Stream roles defined

- **`dopemux:events`** — the raw ingress bus. Sole writer after the reroute: the bridge's
  `/events` handler. Retention-limited; internal transport detail, no external consumer
  contract.
- **`activity.events.v1`** — the versioned, named consumer contract. The bridge publishes
  normalized/curated activity events here; consumers (chronicle mirror → `work_log`,
  adhd-engine, dashboards) read **only** this stream. Schema changes bump the stream
  version suffix, never mutate v1 semantics.

Producers never write either stream directly; consumers never read `dopemux:events`.

### 4. mcp-capture retired

`mcp-capture` is **retired** (register MCP-CAPTURE → `retired`, decision
`adr:adr-mcpint-004`): a second capture door recreates exactly the two-contract drift that
emptied the chronicle. Its good ideas — SHA256 dedup (register DMEM-EVENT-DEDUP),
lane-awareness, capture audit — fold into the `capture_client` backlog as library
features, not a server.

### Invariants

- Exactly one ingress door (`/events`, authenticated) and one producer library
  (`capture_client`).
- No event without per-request workspace/instance identity is accepted.
- No producer holds Redis credentials for the event streams.
- One writer per stream; `activity.events.v1` is the only consumer-facing contract.
- Ingress outage degrades to dropped events (fail-open transport), never blocked callers
  and never silently misattributed writes.

### Non-goals

- The identity mechanism itself (owner: DMX-MEMSPINE-IDENTITY-005 — this ADR consumes its
  contract).
- task.*/workflow event producers (owner: DMX-MEMSPINE-TASKCREATED-003) and
  progress→chronicle spine completion (owner: DMX-MEMSPINE-PROGRESS-CHRONICLE-004) — they
  gain a blessed door here, nothing more.
- Consumer-side rate limits/backpressure (owner: ADR-221).
- ENABLE_MIRROR_SYNC / Trinity Rule 2 indexing flags (owners: MEMSPINE packets; verified
  OFF at P0 claims 9/10 — flipping them is not this ADR's call).
- The bridge's other hazards (secret-leaking `/ddg/decisions` proxy; its resident 4th
  complexity scorer — the latter dies under ADR-MCPINT-001 G5).

## Alternatives Considered

- **G2(b) — ADR-bless direct Redis and delete the dead bridge path.** Rejected by user
  decision: cheapest, but every producer needs Redis creds and identity discipline becomes
  per-producer convention rather than door-enforced — N2 shows convention already failed.
- **G2(c) — split by locality (in-compose → Redis; host/hooks → bridge).** Rejected: two
  contracts to keep honest is how `dopemux:events` and `activity.events.v1` diverged in
  the first place.
- **Keep mcp-capture as the ingress MCP surface instead of the bridge.** Rejected
  (placement map): it is a second door with no auth story, registered nowhere, and
  MCP-shaped ingress invites agents to publish events directly — producers should go
  through a library with enforced identity, not a tool surface.
- **Fail-closed transport (block callers when the bridge is down).** Rejected: turns a
  telemetry outage into a fleet-wide workflow outage; identity is where fail-closed
  belongs, transport is where fail-open belongs.

## Consequences

- **Packets**: MCPINT-IMP-EVENTS-006 (JWT fix: user-store seeding + service tokens +
  blessed `/events` + ConPort reroute + direct-path deprecation), MCPINT-FND-HYG-007
  (producer heartbeat limit; mcp-capture register-or-shelve resolves here as `retired`).
  Cross-tree: DMX-MEMSPINE-IDENTITY-005 (identity contract — BLOCKS the reroute),
  DMX-ADHDLOOP-HOOKINGRESS-001 (hooks→`/external-activity` is a separate SVCFIN-owned
  ingress for ADHD activity; it should adopt `capture_client` semantics but is not folded
  into `/events` by this ADR).
- The chronicle spine becomes trustworthy end-to-end only when this + IDENTITY-005 +
  MEMSPINE mirror work all land — this ADR contributes the door, not the whole spine
  (D.5's "memory that returns without being summoned" chain: decision → chronicle →
  dope-context → next-session recap, consumed by ADR-MCPINT-003 block 2).
- Operational: the bridge becomes ingress-critical; its health belongs in the
  ADR-MCPINT-003 fleet-capability line. Token lifecycle is new operator surface (issuance,
  rotation, revocation) — small, but real.
- Deleting the direct-Redis path breaks any producer that never migrated — the deprecation
  window exists precisely to flush these out loudly.
- ADR-dopecon-bridge-narrowing (adapter-only role) is refined, not contradicted: ingress
  adapter is squarely an adapter duty; the bridge gains no business logic beyond
  normalize-and-publish.

## Migration Strategy

1. IDENTITY-005 lands the per-request identity contract (cross-tree dependency).
2. IMP-EVENTS-006 step 1: seed user store, issue service tokens, integration-test an
   authenticated POST `/events` → `activity.events.v1` → chronicle `work_log` round trip.
3. Step 2: switch `capture_client` transport to `/events` (identity fail-closed, transport
   fail-open); reroute ConPort emission.
4. Step 3: deprecation window for direct Redis (log-on-use), then delete the path and
   revoke producer Redis creds.
5. FND-HYG-007: heartbeat limiter in `capture_client`; retire mcp-capture (register flip +
   source disposition per hygiene convention).
6. Rollback: re-enable the direct-Redis code path from git (it is deleted last, after the
   round-trip proof holds for the deprecation window).

## Verification

- Unauth POST `/events` → 401 (unchanged, now *with* a seeded store behind it); authed
  POST with identity → 2xx and a `work_log` row attributed to the **request's** workspace,
  not the container env (the N2 regression test).
- Identity-less authed POST → 4xx (fail-closed identity).
- Bridge stopped → producer call returns without blocking, event dropped, no exception
  (fail-open transport).
- Heartbeat flood test → producer-side coalescing keeps stream growth bounded.
- `grep` gate: no direct Redis stream writes outside `capture_client`'s transport module;
  no `mcp-capture` references in catalog/configs.
- P6 chronicle e2e: `log_decision` → chronicle row → dope-context hit → next-session recap
  contains it.

## Validation

- **PAL consensus (2026-07-17, pal-stdio `consensus`, continuation
  `523bd511-4906-4bdf-a289-603f9c63da9b`)**: **RUN — both models endorse; no
  blocking objection.**
  - `anthropic/claude-opus-4.1` via OpenRouter (stance: for) — verdict:
    **architecturally sound** (confidence 8/10); the fail-open-transport /
    fail-closed-identity polarity called "precisely correct". Strongest objection:
    operator-seeded service tokens are a bootstrap tactic, not durable auth — wants a
    named evolution path to infrastructure-managed service identity (mTLS/OIDC)
    before fleet scale. Disposition: hardening feedback on MCPINT-IMP-EVENTS-006's
    token-issuance design; single-operator deployment makes the manual lifecycle
    acceptable now.
  - `openai/gpt-5` via OpenRouter (stance: against) — verdict: **"holds as written"
    with one critical caveat** (confidence 8/10). Strongest objection: blanket
    fail-open transport risks silent, irreversible loss of business-relevant events
    during bridge brownouts; demands bounded non-blocking local buffering + drop
    accounting/metrics, server-side token-scope→workspace authorization (reject
    cross-tenant writes even with a valid token), DLQ, and explicit
    ordering/idempotency semantics. Disposition: execution hardening fed to
    MCPINT-IMP-EVENTS-006 verification (drop counters, scope-checked authz) — the
    fail-open polarity itself stands per the ADR's rejected-alternatives rationale.
- ConPort `log_decision`: owed at acceptance.

## Cross-references

- ADR-MCPINT-001 (G5 kills the bridge's resident complexity scorer; catalog records bridge
  as infra), ADR-MCPINT-002 (agents never publish events — no event tool in any exposure
  row), ADR-MCPINT-003 (capability line carries bridge health; hook-produced activity
  rides this ingress), ADR-MCPINT-005 (shelf; DMEM-EVENT-DEDUP ideas absorbed here).
- ADR-221 (consumer-side rate limits — complementary, untouched);
  adr-dopecon-bridge-narrowing-to-adapter-only-role;
  adr-dope-memory-as-chronicle-memory-authority.
- `docs/03-reference/mcp/tool-placement-map.md` §3 (mcp-capture RETIRE row).
- Owners referenced, not decided for: DMX-MEMSPINE-IDENTITY-005,
  DMX-MEMSPINE-TASKCREATED-003, DMX-MEMSPINE-PROGRESS-CHRONICLE-004,
  DMX-ADHDLOOP-HOOKINGRESS-001.
- Runtime evidence: P0 claims 7, 9, 10; findings N2, N5; chronicle-mirror runtime proof
  (2026-07-07: `dopemux:events`=3489 / `activity.events.v1`=0 / `work_log`=0 pre-fix).
