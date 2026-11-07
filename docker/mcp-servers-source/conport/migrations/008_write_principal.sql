-- Migration 008: Write principal (Wave 2A R2, W02)
-- Purpose: record WHO wrote a row. The ConPort server stores the verified
--          principal of the bearer token (for example 'runner:codex') or the
--          literal 'unverified' on every write it makes to these tables.
-- Operator-run only. Never applied on container start (see conport_migration_gate.py).
--
-- Properties:
--   * nullable column with a constant default: a metadata-only change on
--     PostgreSQL 11+, no existing row is rewritten, and rows written before
--     the migration read back as 'unverified';
--   * idempotent (ADD COLUMN IF NOT EXISTS), so a psql-then-adopt run and a
--     re-run are both safe;
--   * the server keeps working before this migration is applied: in 'log' and
--     'off' auth modes it writes without the column, and it reports
--     auth_principal_column=missing on /health; in 'enforce' mode it rejects
--     writes with 503 until the column exists.
--
-- Rollback: migrations/008_rollback.sql (drops the four columns; rows keep
--           all other data).
--
-- Apply by hand on a database where `conport_migration_gate.py apply` would
-- deadlock (fresh databases), then record it with the gate:
--   psql -v ON_ERROR_STOP=1 -d "$DATABASE_URL" -f migrations/008_write_principal.sql
--   DPMX_CONPORT_MIGRATION_APPLY=1 python migrations/conport_migration_gate.py apply   # adopts 008
--   python migrations/conport_migration_gate.py verify

BEGIN;

ALTER TABLE workspace_contexts
    ADD COLUMN IF NOT EXISTS write_principal VARCHAR(255)
    DEFAULT 'unverified';

ALTER TABLE decisions
    ADD COLUMN IF NOT EXISTS write_principal VARCHAR(255)
    DEFAULT 'unverified';

ALTER TABLE progress_entries
    ADD COLUMN IF NOT EXISTS write_principal VARCHAR(255)
    DEFAULT 'unverified';

ALTER TABLE custom_data
    ADD COLUMN IF NOT EXISTS write_principal VARCHAR(255)
    DEFAULT 'unverified';

-- Verify all four columns exist
DO $$
DECLARE
    column_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND column_name = 'write_principal'
      AND table_name IN ('workspace_contexts', 'decisions', 'progress_entries', 'custom_data');

    IF column_count <> 4 THEN
        RAISE EXCEPTION 'Migration 008 failed: expected 4 write_principal columns, found %', column_count;
    END IF;

    RAISE NOTICE 'Migration 008 completed successfully';
END $$;

COMMIT;
