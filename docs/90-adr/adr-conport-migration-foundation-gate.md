---
id: adr-conport-migration-foundation-gate
title: "ADR: ConPort migration foundation gate"
type: adr
owner: '@hu3mann'
author: '@codex'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Records the decision to gate DMX-CONPORT-OPTIMAL on explicit migration-state proof before downstream ConPort feature packets execute.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-memory-trinity-authority-and-interaction-model
---

# ADR: ConPort migration foundation gate

**Status:** Proposed
**Date:** 2026-06-16
**Decision Type:** Architecture / Migration Safety / Task Packet Sequencing
**Scope:** ConPort, DMX-CONPORT-OPTIMAL task packets, repo load-plan artifacts

## Context

DMX-CONPORT-OPTIMAL contains downstream packets that depend on enhanced ConPort
schema objects. Current source evidence does not prove those objects are applied
by the runtime startup path:

- ConPort startup calls `_ensure_schema()`.
- `_ensure_schema()` checks only for `public.workspace_contexts` before
  returning.
- If the sentinel table is missing, startup applies `/app/schema.sql`.
- The Dockerfile copies `schema.sql`, but does not copy the migrations
  directory.
- Enhanced objects such as `decision_relationships`, `review_reminders`,
  `adhd_metrics`, and multi-tenancy tables live in migration files outside the
  observed startup bootstrap.

This creates a hidden prerequisite for downstream packets and weakens
replayability.

## Decision

Add `DMX-CONPORT-OPTIMAL-100-migration-foundation-gate` before
`DMX-CONPORT-OPTIMAL-101-server-bringup-smoke`.

Packet 100 must prove or fail closed on:

- migration file availability in the execution context,
- deterministic migration apply or verify behavior,
- migration ledger/checksum or equivalent drift detection,
- rebuild-from-zero behavior,
- partial migration handling,
- read-only live database introspection where available,
- PAL gate availability and review status.

The repo load plan is updated so packet 100 blocks packet 101. Existing packet
IDs and orchestrator UUID mappings remain unchanged.

## Non-decision

This ADR does not authorize silent migration auto-apply on normal ConPort
startup. Any runtime migration runner must be explicit, operator-gated,
auditable, and fail closed on drift.

This ADR also does not mutate live task-orchestrator state. Synchronizing the
already-loaded root is a separate operator action and must not be claimed from
repo artifact changes alone.

## Consequences

- Packet 100 becomes the first intended execution gate for the repo load plan.
- Schema-dependent packets must cite packet 100 proof before execution.
- Live queue state may remain stale until a separate orchestrator sync occurs.
- Hardening-series expansion remains deferred until migration foundation proof
  exists.
