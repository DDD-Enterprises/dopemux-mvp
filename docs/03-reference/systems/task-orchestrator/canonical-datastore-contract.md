---
id: canonical-datastore-contract
title: Canonical Datastore Contract
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: Canonical Datastore Contract (reference) for dopemux documentation and developer
  workflows.
---
# Task Orchestrator Canonical Datastore Contract

## Scope

This contract defines an offline reconciliation datastore for safe Task Orchestrator evidence packs. It is not a live workflow writer and it does not make Task Orchestrator the single PM authority.

## Authority Boundaries

- Task Orchestrator: workflow views, workflow roles, and transition memory.
- Leantime: passive PM metadata authority.
- ConPort: structured decision, progress, context, and custom-data authority.
- dope-memory: chronicle and evidence receipt authority.
- dopecon-bridge: adapter, proxy, and transport boundary only.

## Store Rules

- Every imported row keeps source provenance: `source_db_slug`, `source_database_path`, `source_schema_hash`, `source_table`, `source_row_id`, `source_mtime_utc`, `import_run_id`, and `archive_sha256`.
- Modern and legacy source schemas are both recorded. Legacy and recovery rows stay provenance-only unless an explicit reconciliation decision promotes them.
- Raw note bodies and FTS rows are excluded. Note bodies are represented only by redacted length/hash handles from the safe pack.
- `canonical_current_work_items` is a materialized view table built only from the active dopemux source after `--resolve-current`.
- Duplicate titles are conflicts or aliases, not canonical identity.

## Field Sensitivity

- `work_item.title` and `work_item.summary` are imported as **source-provided fields, verbatim** unless redacted upstream. They are not raw note bodies, but may contain sensitive text if upstream authors placed it there.
- Safe-pack redaction excludes note bodies, descriptions, metadata/properties, and FTS rows. It does **not** redact titles or summaries — treat them as source-trust, not secret-free.

## JSON Schema Contracts

Two committed JSON schemas describe this datastore. Both are JSON Schema **draft 2020-12** and are exercised by `tests/task_orchestrator/test_canonical_datastore_json_schema.py`.

- `schemas/task-orchestrator/canonical-datastore.schema.json` — the **datastore manifest** contract. The reusable `provenance` `$defs` is intentionally open; closure is applied on the composed `source_database` / `imported_entity` objects via `unevaluatedProperties: false`, so provenance fields plus the `allOf` extension fields validate while unexpected fields are rejected.
- `schemas/task-orchestrator/reconciliation-decision.schema.json` — models the **emitted coldstart reconciliation artifact** (`COLDSTART_RECONCILIATION.json`). It previously modeled the un-emitted `reconciliation_decisions` SQL table; it was repurposed to the artifact the importer actually emits so committed evidence validates against a real, enforced contract. Its `decision`/`classification` enums are derived from the resolver code paths in `tools/task_orchestrator_reconcile/resolve.py`.

## Manifest

`import_pack --emit-manifest <path>` writes a `CANONICAL_DATASTORE_MANIFEST.json` conforming to `canonical-datastore.schema.json`:

- `source_pack`: `archive_sha256`, deterministic `generated_at_utc` (newest source mtime, never wall-clock), and `redacted_only`.
- `source_databases`: one provenance-only summary per staged source DB (provenance fields + `schema_class` / `adjudication_class` / `canonical_treatment`).
- `imported_entities`: provenance-only summaries of the **derived** `canonical_current_work_items` (entity type `canonical_current_work_item`) — not the raw imported source rows. No titles, summaries, or note bodies are included in the manifest.
- `redaction_policy`: declares note bodies and FTS rows excluded and free-form descriptions reduced to redacted hash handles.

## Runtime Impact

Default runtime behavior is unchanged. The importer writes only to a caller-supplied offline SQLite file and never opens live `current-tasks.db` files.
