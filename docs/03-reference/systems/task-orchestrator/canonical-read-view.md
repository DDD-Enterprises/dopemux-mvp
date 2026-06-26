---
id: canonical-read-view
title: Canonical Reconciliation Read View
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-23'
last_review: '2026-06-23'
next_review: '2026-09-21'
prelude: Canonical Reconciliation Read View (reference) for dopemux documentation and developer
  workflows.
---
# Canonical Reconciliation Read View

A feature-flagged, **read-only** operator view over the **offline** canonical reconciliation SQLite
artifact produced by `tools/task_orchestrator_reconcile/import_pack.py` (`--output`). It is a **DERIVED,
point-in-time** view — it is **never** live state, **never** a canonical or PM authority, and **never** a
Task Orchestrator writer. See [canonical-datastore-contract.md](canonical-datastore-contract.md) for the
authority boundaries.

## What it is (and is not)

- **Is:** a way to inspect the rows the offline importer materialized (`canonical_current_work_items`) with
  full source provenance, plus a point-in-time anchor.
- **Is not:** a connection to any live `current-tasks.db`; a PM authority; a workflow writer; or a
  registered `canonical_*` runtime authority. `config/runtime_authority_manifest.json` is not touched by
  this surface.

## Feature flag

The command is gated by the `CANONICAL_STORE_READ_VIEW_ENABLED` environment variable, **default off**.
When unset/false it **fails closed** (non-zero exit, clear message) and never opens the SQLite file.

```bash
export CANONICAL_STORE_READ_VIEW_ENABLED=1
```

## Command

```bash
dopemux orchestrator canonical-store inspect --db <offline-canonical.sqlite> [options]
```

The store is opened strictly read-only (`file:<path>?mode=ro`, with the path percent-encoded so URI
metacharacters cannot bypass `mode=ro`). Note bodies / `summary` and FTS rows are never surfaced.

### Options

| Option | Default | Meaning |
|--------|---------|---------|
| `--db PATH` | (required) | Path to the offline canonical reconciliation SQLite file. |
| `--limit INT` | none | Cap items returned; the full `item_count` (store total) is still reported. |
| `--role TEXT` | none | Filter to items with this exact `role`. |
| `--status TEXT` | none | Filter to items with this exact `status_label`. |
| `--root TEXT` | none | Filter to items whose `canonical_identity` starts with this prefix. |
| `--include-terminal` | off | Include terminal-role items (`done`, `cancelled`, `archived`); excluded by default. |
| `--format [table\|json]` | `table` | Output format. |
| `--json-output` | off | Alias for `--format json`. |

All filter values are bound as parameterised SQL placeholders — none are interpolated into SQL.

### Output

The human-readable (table) banner makes the non-live nature explicit:

```text
CANONICAL RECONCILIATION VIEW
  mode: read-only
  source: offline sqlite
  valid_as_of: <MAX(source_mtime_utc) — ISO-8601 UTC, see note below>
  live_state: false
  source_dbs=<N> | items=<store total> | showing=<after filters>
```

Each row carries provenance: `canonical_identity`, `role`, `status_label`, `source_db_slug`,
`source_row_id` (JSON output additionally includes `title`, `source_mtime_utc`, `import_run_id`,
`archive_sha256`).

### `valid_as_of` semantics

`valid_as_of` is `MAX(source_mtime_utc)` over `source_databases`. This is a lexicographic string MAX and
equals the true chronological maximum only because `import_pack` emits zero-padded ISO-8601 UTC mtimes.

## Examples

```bash
# Default table view (terminal items excluded)
dopemux orchestrator canonical-store inspect --db /tmp/to-canonical-full-dryrun.sqlite

# JSON, only work items, first 20
dopemux orchestrator canonical-store inspect --db /tmp/store.sqlite --role work --limit 20 --format json

# Items under a series prefix, including terminal
dopemux orchestrator canonical-store inspect --db /tmp/store.sqlite --root TP-TO-CANON --include-terminal
```

## Authority note

This view is **derived/read-only/point-in-time**. It does not own PM truth, does not write workflow state,
and does not promote the offline store into a live authority. PM authority remains split across Leantime,
task-orchestrator, ConPort, dope-memory, dope-context, and the dopecon-bridge transport boundary.
