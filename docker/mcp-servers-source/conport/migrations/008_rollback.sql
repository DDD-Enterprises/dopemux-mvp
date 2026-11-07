-- Rollback Migration 008: remove the write principal columns
-- Purpose: undo 008_write_principal.sql. Only the four write_principal columns
--          are dropped; every other column and row is untouched, so data
--          written while the column existed keeps its content (it loses only
--          the principal that wrote it).
-- Operator-run only. Not discovered by conport_migration_gate.py (rollback files are skipped).
--
-- After running this, remove the ledger row so the gate does not report a
-- stale adoption:
--   DELETE FROM conport_schema_migrations WHERE version = 8;
-- and set CONPORT_AUTH_MODE to 'off' or 'log' first: in 'enforce' mode the
-- server rejects writes (503) while the column is missing.

BEGIN;

ALTER TABLE workspace_contexts DROP COLUMN IF EXISTS write_principal;
ALTER TABLE decisions DROP COLUMN IF EXISTS write_principal;
ALTER TABLE progress_entries DROP COLUMN IF EXISTS write_principal;
ALTER TABLE custom_data DROP COLUMN IF EXISTS write_principal;

DO $$
DECLARE
    column_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND column_name = 'write_principal'
      AND table_name IN ('workspace_contexts', 'decisions', 'progress_entries', 'custom_data');

    IF column_count <> 0 THEN
        RAISE EXCEPTION 'Rollback 008 failed: % write_principal columns remain', column_count;
    END IF;

    RAISE NOTICE 'Rollback 008 completed successfully';
END $$;

COMMIT;
