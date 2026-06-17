---
id: proof-dmx-conport-optimal-100-migration-foundation-gate
title: "DMX-CONPORT-OPTIMAL-100 migration foundation gate proof"
type: proof
owner: '@hu3mann'
author: '@codex'
date: '2026-06-16'
last_review: '2026-06-17'
next_review: '2026-09-14'
prelude: Proof bundle for live packet 100 execution and repo-side migration gate implementation. Live apply remains operator-gated and not run.
---

# DMX-CONPORT-OPTIMAL-100 migration foundation gate proof

## Result

**REPO-SIDE GATE IMPLEMENTED / LIVE APPLY NOT_RUN.**

Packet 100 originally failed closed because evidence did not prove ConPort
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

Follow-up implementation added an explicit operator-run migration gate:

- `docker/mcp-servers-source/conport/conport_migration_gate.py`
- `docker/mcp-servers-source/conport/tests/test_migration_gate.py`
- Dockerfile copy lines for `conport_migration_gate.py` and `migrations/`
- Packet 100 allowlist and verification commands for the new gate and tests

The gate is not wired into normal ConPort startup and does not silently apply
migrations. Default mode is read-only verification; mutation requires
`--apply`. Live `--apply` was not run in this pass because live DB mutation
requires explicit operator approval and task-orchestrator transport was not
available for final live progression.

## Live item

- Root: `44452f53-615d-4519-b21a-4a9cbc8774a4`
- Packet 100: `dcf66b56-8fbf-426f-a6d6-826f0caa5822`
- Role before execution: `queue`
- Role after start: `work`
- Final action: block/fail-closed, not complete

## Original blocker source evidence

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

## Follow-up repo-side implementation evidence

Dockerfile now copies the gate and migrations into the image build context:

```text
COPY docker/mcp-servers-source/conport/conport_migration_gate.py .
COPY docker/mcp-servers-source/conport/migrations ./migrations
```

The migration gate implementation includes:

- foundation migration scope fixed to `001_enhanced_decision_model.sql`,
  `002_decision_patterns_table.sql`, and
  `003_multi_tenancy_foundation.sql`,
- SHA-256 checksum calculation for each migration file,
- `conport_schema_migrations` ledger rows with rank, checksum, status, and
  error text,
- default read-only verify mode that fails if the ledger is missing,
- explicit `--apply` mode for schema mutation,
- PostgreSQL advisory lock during apply,
- schema checks for downstream foundation tables, views, and columns,
- no hard-coded database URL; `POSTGRES_URL`, `DATABASE_URL`, or
  `--database-url` is required.

Focused tests validate URL normalization, migration discovery ordering and
scope, missing-file fail-closed behavior, checksum drift sensitivity, and
required schema check coverage.

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

Follow-up PAL:

- `pal.thinkdeep` confirmed verify mode should be no-write and fail when the
  ledger is absent, `--apply` may create the ledger and apply known foundation
  migrations, and startup should remain unchanged.
- `pal.planner` produced the mutation sequence for tests, runner, Dockerfile,
  packet metadata, proof, validation, and live apply boundary.
- `pal.consensus` consulted three stances. Two favored new packet 100; all
  rejected dossier-only. The dissenting stance warned that future enhanced-table
  runtime consumers must check durable gate state to avoid enforcement drift.
- `pal.codereview` and `pal.precommit` were invoked after edits, but the PAL
  tools requested embedded file contents and did not provide line-specific
  external findings. Treat those as LIMITED PAL checks, not full external
  approval.
- Final `pal.challenge` was invoked to attack overclaiming. The resulting proof
  keeps live DB apply, live packet completion, and downstream unblocking as
  NOT_RUN until operator-gated live verification succeeds.

## Blocker

The original deterministic-runner blocker is addressed in repo code, but packet
100 still cannot be completed live until the operator-gated database path is
run and verified:

- run the gate in verify mode against a live ConPort database,
- if verify fails due missing ledger/schema and operator approves mutation, run
  `--apply`,
- rerun verify and confirm ledger/checksum/schema state,
- update live task-orchestrator packet 100 proof and status.

## Validation

PASS:

- `python3 -m json.tool task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate.json >/dev/null`
- `python3 -m jsonschema -i task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `PYTHONPATH=docker/mcp-servers-source/conport python3 -m pytest docker/mcp-servers-source/conport/tests/test_migration_gate.py -q`
- `python3 -m py_compile docker/mcp-servers-source/conport/conport_migration_gate.py`
- `python3 docker/mcp-servers-source/conport/conport_migration_gate.py --help >/dev/null`
- source evidence check confirmed Dockerfile copies gate and migrations and the
  gate contains ledger and advisory lock code
- `git diff --check`

FAIL:

- `python3 docker/mcp-servers-source/conport/conport_migration_gate.py --json`
  returned exit code 1 with `{"error": "POSTGRES_URL or DATABASE_URL is required", "status": "failed"}`.
  This is expected fail-closed behavior when no DB URL is supplied.

NOT_RUN:

- Live DB `--apply`: requires explicit operator approval for schema mutation.
- Live task-orchestrator packet completion/update: task-orchestrator transport
  was unavailable during this pass.
