---
id: CONPORT_REAL_IMPORT_INTEGRITY_2026_02_06
title: ConPort Real Import Integrity 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Pre/post integrity evidence for the first non-dry-run import of historical ConPort SQLite snapshot data into postgres-age.
---
# ConPort Real Import Integrity (2026-02-06)

## Source

- Import bundle: `reports/conport_sqlite_exports/20260206T144006Z/import_bundles/quarantine__2026-02-04__SYSTEM_ARCHIVE__db_backups__context_20251024_181450_db__conport_import_bundle.json`
- SHA256: `2b658ebd55676e014efe1c4f345645781e4b54db63d48968218967dcbf934803`
- DB target: `dopemux-postgres-age` (`dopemux_knowledge_graph`)

## Payload Counts

- decisions: 294
- progress_entries: 209
- custom_data: 14
- context_links: 111
- system_patterns: 3
- active_context: 1
- product_context: 1

## Integrity Check (Pre/Post)

| Table | Pre | Post | Delta |
|---|---:|---:|---:|
| `public.decisions` | 1 | 295 | +294 |
| `public.progress_entries` | 1 | 210 | +209 |
| `public.custom_data` | 2 | 15 | +13 |
| `public.entity_relationships` | 0 | 0 | +0 |
| `public.workspace_contexts` | 1 | 2 | +1 |

## Observations

1. Core record families imported successfully (`decisions`, `progress_entries`, `custom_data`).
2. `custom_data` delta is lower than payload count because one key was upserted over an existing row.
3. `workspace_contexts` accepted one row and rejected `product_context` in this run due unique `workspace_id`.
4. `context_links` did not materialize as `entity_relationships` in this run.

## Follow-up Fixes Added in Code After This Run

1. Importer schema detection now supports both `ag_catalog` and `public`.
2. Importer now adapts inserts to discovered columns per table.
3. Progress-entry IDs now join the ID mapping (required for relationship restoration).
4. Single-row `workspace_contexts` schemas now use combined-context upsert behavior.

## Relationship Backfill Closure

Executed with `scripts/deploy/migration/backfill_conport_relationships.py` against the same bundle and workspace.

1. `context_links_total`: 111
2. first pass inserted: 110 (1 skipped custom_data edge case)
3. second pass inserted: 1, deduplicated: 110 (idempotent closure run)
4. skipped after final run: 0
5. live table count moved from `0` to `111`

This closes the previously open relationship-restoration gap to 100% parity for this bundle.

## Evidence Artifact

- `reports/strict_closure/conport_real_import_integrity_2026-02-06.json`
- `reports/strict_closure/conport_backlog_extract_2026-02-06.json`
- `reports/strict_closure/conport_relationship_backfill_2026-02-06.json`
