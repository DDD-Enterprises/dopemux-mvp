---
id: proof-dmx-conport-optimal-100-migration-foundation-gate
title: "DMX-CONPORT-OPTIMAL-100 migration foundation gate proof"
type: proof
owner: '@hu3mann'
author: '@codex'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Proof bundle for live packet 100 execution. The gate fails closed because migration application and enhanced schema state are not proven.
---

# DMX-CONPORT-OPTIMAL-100 migration foundation gate proof

## Result

**FAIL-CLOSED / BLOCKED.**

Packet 100 must not be completed yet. Current evidence does not prove ConPort
migration foundation readiness:

- The Dockerfile copies `schema.sql` but does not copy the `migrations/`
  directory.
- `_ensure_schema()` checks only for `public.workspace_contexts` and applies
  only `/app/schema.sql`.
- `schema.sql` lacks enhanced migration objects such as
  `decision_relationships`.
- Migration files define the enhanced objects, but no deterministic live apply
  path or ledger/checksum verifier is proven.
- Live DB introspection shows `ag_catalog` and baseline public tables, but the
  inspected enhanced migration tables are absent.

## Live item

- Root: `44452f53-615d-4519-b21a-4a9cbc8774a4`
- Packet 100: `dcf66b56-8fbf-426f-a6d6-826f0caa5822`
- Role before execution: `queue`
- Role after start: `work`
- Final action: block/fail-closed, not complete

## Source evidence

Dockerfile copies ConPort runtime files and `schema.sql`:

```text
29 # Copy the enhanced server with PostgreSQL + Redis persistence (relative to root)
30 COPY docker/mcp-servers-source/conport/server.py .
31 COPY docker/mcp-servers-source/conport/enhanced_server.py .
32 COPY docker/mcp-servers-source/conport/instance_detector.py .
33 COPY docker/mcp-servers-source/conport/integration_bridge_client.py .
34 COPY docker/mcp-servers-source/conport/conport_mcp_stdio.py .
35 COPY docker/mcp-servers-source/conport/schema.sql .
36 COPY docker/mcp-servers-source/conport/info_server.py .
37 COPY docker/mcp-servers-source/conport/start_with_info.sh .
```

No `COPY docker/mcp-servers-source/conport/migrations` line is present.

`_ensure_schema()` uses `workspace_contexts` as the readiness sentinel and
applies `/app/schema.sql` only:

```text
408 async def _ensure_schema(self) -> None:
409     """Ensure required tables exist; apply schema.sql via psql if missing."""
413     SELECT 1 FROM information_schema.tables
414     WHERE table_schema = 'public' AND table_name = 'workspace_contexts'
418 if exists:
419     logger.info("Database schema present (workspace_contexts found)")
420     return
422 logger.info("Database schema missing - applying /app/schema.sql")
435 # Apply schema using psql with ON_ERROR_STOP
449 "/app/schema.sql",
```

Structured source checks:

```text
Dockerfile copies schema.sql: True
Dockerfile copies migrations directory: False
_ensure_schema checks workspace_contexts sentinel: True
_ensure_schema applies /app/schema.sql: True
schema.sql has decision_relationships: False
migration001 has decision_relationships: True
migration001 has review_reminders: True
migration003 has user_workspace_access: True
```

## Live DB evidence

Read-only metadata introspection was run through in-container `psql`.

Observed schemas/tables include:

```text
ag_catalog.ag_graph
ag_catalog.ag_label
public.custom_data
public.decisions
public.entity_relationships
public.progress_entries
public.search_cache
public.session_snapshots
public.workspace_contexts
```

`ag_catalog` exists.

Observed ConPort baseline columns include `decisions.id` as `uuid` and
`entity_relationships.source_id` / `target_id` as `uuid`.

The inspected output did not include these enhanced migration tables:

```text
decision_relationships
review_reminders
adhd_metrics
decision_patterns
users
workspaces
user_workspace_access
```

`entity_relationships` constraints in the inspected set are primary key,
not-null checks, and `entity_relationships_strength_check`; no FK or
relationship-type vocabulary CHECK was observed.

## PAL evidence

PAL analyze:

- Identified missing migration runner/ledger and absent enhanced live schema as
  a high-severity reason not to complete packet 100.

PAL thinkdeep:

- Confirmed packet 100 should be blocked/fail-closed.
- Recommended proof include Dockerfile copy evidence, `_ensure_schema()`
  behavior, schema-vs-migration object split, live DB introspection, and
  concrete unblock criteria.

## Blocker

Packet 100 cannot be completed until ConPort has a deterministic migration
foundation:

- migrations are available in the execution/runtime context,
- migrations are applied or verified in a deterministic order,
- migration state has ledger/checksum or equivalent drift detection,
- live DB enhanced objects exist or the verifier fails closed,
- partial migration and drift behavior are documented and tested.

## Minimal unblock criteria

One of these must be implemented and proven:

- Preferred: copy `migrations/` into the image and add an explicit,
  operator-gated migration runner/verifier with ledger/checksum drift detection.
- Alternative: fold required migration SQL into the bootstrap path so
  `schema.sql` matches the runtime expectations, with explicit drift checks.

Until then, downstream DMX-CONPORT-OPTIMAL work remains blocked by packet 100.
