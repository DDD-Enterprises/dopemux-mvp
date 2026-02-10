-- Packet D Schema Migration: Add provenance fields to work_log_entries
-- Version: v1.1.0
-- Purpose: Enable explainability for all promoted memories per Packet D §4

-- Step 1: Add provenance columns (nullable during migration)
ALTER TABLE work_log_entries ADD COLUMN source_event_id TEXT;
ALTER TABLE work_log_entries ADD COLUMN source_event_type TEXT;
ALTER TABLE work_log_entries ADD COLUMN source_adapter TEXT;
ALTER TABLE work_log_entries ADD COLUMN source_event_ts_utc TEXT;
ALTER TABLE work_log_entries ADD COLUMN promotion_rule TEXT;
ALTER TABLE work_log_entries ADD COLUMN promotion_ts_utc TEXT;
ALTER TABLE work_log_entries ADD COLUMN supersedes_entry_id TEXT;

-- Step 2: Add reflection provenance
ALTER TABLE reflection_cards ADD COLUMN source_entry_ids_json TEXT DEFAULT '[]';

-- Step 3: Backfill legacy rows with sentinel values
-- Per Packet D §7.8: Sentinels mark pre-migration entries without lying about provenance
UPDATE work_log_entries
SET
  source_event_id = 'pre_migration',
  source_event_type = 'unknown',
  source_adapter = 'unknown',
  promotion_rule = 'unknown',
  source_event_ts_utc = created_at_utc,
  promotion_ts_utc = created_at_utc
WHERE source_event_id IS NULL;

-- Step 4: Update reflection cards
UPDATE reflection_cards
SET source_entry_ids_json = '[]'
WHERE source_entry_ids_json IS NULL;

-- Step 5: Version bump
INSERT OR REPLACE INTO schema_migrations (version, applied_at_utc)
VALUES ('v1.1.0', datetime('now'));

-- Note: NOT NULL constraints are enforced in application layer for new writes.
-- SQLite does not easily support adding NOT NULL to existing columns without table rebuild.
-- Runtime code MUST enforce NOT NULL and reject sentinels for all post-migration promotions.
