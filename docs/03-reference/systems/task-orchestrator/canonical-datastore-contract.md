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

## Runtime Impact

Default runtime behavior is unchanged. The importer writes only to a caller-supplied offline SQLite file and never opens live `current-tasks.db` files.
