---
id: CONPORT_SQLITE_EXTRACTION_2026_02_06
title: Conport Sqlite Extraction 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: SQLite ConPort data extraction summary with manifest references and exported table counts for migration and validation workflows.
---
# ConPort SQLite Extraction (2026-02-06)

## Purpose

Extract all actionable ConPort SQLite data into portable artifacts for migration, verification, and recovery workflows.

## Export Command

```bash
python scripts/export_conport_sqlite_snapshot.py
```

## Output Root

- `reports/conport_sqlite_exports/20260206T143748Z/`
- Manifest: `reports/conport_sqlite_exports/20260206T143748Z/manifest.json`

## Databases Exported

1. `context_portal/context.db` (5.0 MB)
2. `.dopemux/context.db` (32 KB)

## Extracted Row Totals

- Total rows exported: `1399`
- `context_portal/context.db`: `1399`
- `.dopemux/context.db`: `0`

## Table Counts (`context_portal/context.db`)

- `decisions`: `420`
- `progress_entries`: `496`
- `custom_data`: `52`
- `context_links`: `166`
- `system_patterns`: `7`
- `active_context`: `1`
- `active_context_history`: `252`
- `product_context`: `1`
- `product_context_history`: `3`
- `alembic_version`: `1`

## Notes

- FTS shadow tables were excluded by default (`--include-fts` can include them).
- Each exported table is stored as JSONL with per-file SHA256 hashes in the manifest.
- This extraction is read-only and does not mutate SQLite source databases.
