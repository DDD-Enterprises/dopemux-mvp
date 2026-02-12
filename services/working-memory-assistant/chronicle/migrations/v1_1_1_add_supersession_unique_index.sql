-- Packet F Schema Migration: Enforce linear supersession chains
-- Version: v1.1.1
-- Purpose: Prevent branching in supersession chains at the database level
-- Reference: DESIGN_DELTA_supersession_correction_semantics.md §3.2, §9.1

-- Enforce linear supersession chains (no branching)
-- NULLs are excluded from UNIQUE in SQLite, so multiple NULL entries are permitted.
-- Only one non-NULL entry may reference any given supersedes_entry_id.
CREATE UNIQUE INDEX IF NOT EXISTS idx_worklog_supersedes_unique
  ON work_log_entries(supersedes_entry_id)
  WHERE supersedes_entry_id IS NOT NULL;

-- Version bump
INSERT OR IGNORE INTO schema_migrations (version, applied_at_utc)
VALUES ('v1.1.1', datetime('now'));
