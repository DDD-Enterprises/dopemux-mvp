-- Wave 2A R2 W01: record who wrote each ledger row (design 5.8, B04).
-- Version: v1.3.0
-- Purpose: add a nullable `write_principal` (default 'unverified') and a
--          `write_principal_self_asserted` marker to every table a writer
--          touches. HTTP writers store the principal verified from their
--          bearer token; local writers (eventbus_consumer, hooks) store a
--          self-asserted internal principal; everything else stays
--          'unverified'. Existing rows read as 'unverified' (no rewrite).
--
-- Applied automatically on first use by whichever process opens the ledger
-- first (ChronicleStore.initialize_schema or capture_client). Older readers
-- and writers that name their columns keep working: both columns are
-- nullable-or-defaulted.
--
-- ROLLBACK (run these, one statement per line, then restart the writers on the
-- previous code; rows keep all their other data; SQLite >= 3.35 for DROP COLUMN):
-- ROLLBACK: ALTER TABLE raw_activity_events DROP COLUMN write_principal;
-- ROLLBACK: ALTER TABLE raw_activity_events DROP COLUMN write_principal_self_asserted;
-- ROLLBACK: ALTER TABLE work_log_entries DROP COLUMN write_principal;
-- ROLLBACK: ALTER TABLE work_log_entries DROP COLUMN write_principal_self_asserted;
-- ROLLBACK: ALTER TABLE issue_links DROP COLUMN write_principal;
-- ROLLBACK: ALTER TABLE issue_links DROP COLUMN write_principal_self_asserted;
-- ROLLBACK: ALTER TABLE reflection_cards DROP COLUMN write_principal;
-- ROLLBACK: ALTER TABLE reflection_cards DROP COLUMN write_principal_self_asserted;
-- ROLLBACK: DELETE FROM schema_migrations WHERE version = 'v1.3.0';

ALTER TABLE raw_activity_events ADD COLUMN write_principal TEXT DEFAULT 'unverified';
ALTER TABLE raw_activity_events ADD COLUMN write_principal_self_asserted INTEGER NOT NULL DEFAULT 0;

ALTER TABLE work_log_entries ADD COLUMN write_principal TEXT DEFAULT 'unverified';
ALTER TABLE work_log_entries ADD COLUMN write_principal_self_asserted INTEGER NOT NULL DEFAULT 0;

ALTER TABLE issue_links ADD COLUMN write_principal TEXT DEFAULT 'unverified';
ALTER TABLE issue_links ADD COLUMN write_principal_self_asserted INTEGER NOT NULL DEFAULT 0;

ALTER TABLE reflection_cards ADD COLUMN write_principal TEXT DEFAULT 'unverified';
ALTER TABLE reflection_cards ADD COLUMN write_principal_self_asserted INTEGER NOT NULL DEFAULT 0;

INSERT OR IGNORE INTO schema_migrations (version, applied_at_utc)
VALUES ('v1.3.0', datetime('now'));
