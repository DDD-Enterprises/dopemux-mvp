---
id: conport-optimal-coverage-and-hardening-analysis-2026-06-16
title: "ConPort optimal coverage and migration foundation analysis"
type: analysis
owner: '@hu3mann'
author: '@codex'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Separates observed ConPort migration/runtime evidence from inherited claims and gates DMX-CONPORT-OPTIMAL downstream packets on an explicit migration foundation packet.
---

# ConPort optimal coverage and migration foundation analysis

## Status

This analysis supersedes the earlier no-DAG-change amendment plan for
DMX-CONPORT-OPTIMAL. The prior plan treated the loaded packet graph as safe to
preserve while amending downstream packet text. Current evidence shows a hidden
foundation prerequisite: ConPort migration state is not proven by the runtime
startup path or Docker image contents.

## Authority and evidence

Observed repo authority:

- `docker/mcp-servers-source/conport/enhanced_server.py` calls `_ensure_schema()`
  during startup.
- `_ensure_schema()` checks only for `public.workspace_contexts`; if that table
  exists it returns without applying migration files.
- When the sentinel table is absent, `_ensure_schema()` applies only
  `/app/schema.sql`.
- `docker/mcp-servers-source/conport/Dockerfile` copies `schema.sql` into the
  image, but does not copy `docker/mcp-servers-source/conport/migrations/`.
- `schema.sql` creates the baseline ConPort tables, including
  `workspace_contexts`, `decisions`, `progress_entries`, `session_snapshots`,
  `custom_data`, `entity_relationships`, and `search_cache`.
- Enhanced migration objects are in migration files, not the observed startup
  bootstrap:
  - `001_enhanced_decision_model.sql` creates `decision_relationships`,
    `adhd_metrics`, and `review_reminders`.
  - `003_multi_tenancy_foundation.sql` adds `user_id` columns and creates
    `users`, `workspaces`, and `user_workspace_access`.

Inherited but corrected claims:

- Code-only inference is insufficient for image/runtime claims. A live image may
  contain files or schemas not obvious from a source-only read; any such claim
  must be rechecked against the live container or marked `NOT_RUN`.
- The presence of migration SQL files in the repo does not prove they are copied
  into the image or applied to a live database.
- Downstream packets must not assume enhanced migration objects exist until a
  dedicated foundation gate proves the object set and drift behavior.

Live read-only database check on 2026-06-16:

- `dopemux-postgres-age` was running and queried with in-container `psql`; no
  external credential value is recorded here.
- `ag_catalog` exists with AGE tables `ag_graph` and `ag_label`.
- Public ConPort baseline tables observed: `workspace_contexts`, `decisions`,
  `progress_entries`, `session_snapshots`, `custom_data`,
  `entity_relationships`, and `search_cache`.
- Public enhanced migration tables were not present in the inspected output:
  `decision_relationships`, `review_reminders`, `adhd_metrics`,
  `decision_patterns`, `users`, `workspaces`, and `user_workspace_access`.
- `decisions.id` is `uuid`.
- `entity_relationships` has `source_id` and `target_id` UUID columns and only
  primary-key/not-null/strength constraints in the inspected constraint set.

## Decision

Add `DMX-CONPORT-OPTIMAL-100-migration-foundation-gate` before packet 101.
Packet 100 is the explicit Tier-0 gate for:

- migration file availability,
- deterministic apply/verify behavior,
- ledger/checksum or equivalent drift proof,
- read-only live DB introspection where available,
- fail-closed handling for partial apply, missing objects, checksum mismatch,
  unavailable DB, or unavailable PAL validation.

The repo load plan is updated so packet 100 blocks packet 101. Existing packet
IDs and orchestrator UUID mappings are preserved.

## Live orchestrator caveat

The initial repo change did not mutate the already-loaded task-orchestrator root
`44452f53-615d-4519-b21a-4a9cbc8774a4`.

After separate user authorization on 2026-06-16, live synchronization created
packet 100 as `dcf66b56-8fbf-426f-a6d6-826f0caa5822`. At sync time, live packet
101 was already terminal and packet 102 was already in review, so a literal
`100 -> 101` edge would not enforce the gate. The live sync therefore created
packet 100 blockers to packet 101 and the current non-terminal descendants as
live-state reconciliation. A fresh repo replay remains the cleaner 19-node /
22-edge graph with packet 100 blocking packet 101.

## PAL review summary

Pre-edit PAL tools were run on 2026-06-16:

- `pal.analyze`: identified downstream schema assumptions as a high-severity
  hidden prerequisite.
- `pal.thinkdeep`: confirmed the fail-closed migration foundation gate is the
  safer replayability boundary.
- `pal.challenge`: forced the live-orchestrator caveat into scope.
- `pal.planner`: confirmed the artifact mutation sequence.
- `pal.consensus`: two of three model stances favored packet 100; the opposing
  stance warned that repo DAG edits do not update live orchestrator state.

## Packet implications

Affected packets must require packet 100 evidence before execution:

- 101: bringup smoke must not be treated as the first foundation gate.
- 108: integration test setup must use the packet 100 migration ordering and
  ledger expectations.
- 201, 202, 301, 302, 303: schema-dependent feature packets must fail closed if
  packet 100 did not prove the relevant table/column/constraint state.

Hardening-series expansion remains deferred until packet 100 proves migration
state, rebuild-from-zero behavior, and drift handling.
