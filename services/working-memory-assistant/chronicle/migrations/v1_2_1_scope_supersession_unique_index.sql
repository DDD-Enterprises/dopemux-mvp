-- Packet H: Scope Supersession Unique Index (hardening)
-- Version: v1.2.1
-- Purpose: Scope supersession uniqueness to workspace and instance to prevent cross-workspace contamination.

-- Ensure final state is deterministic:
-- 1) remove legacy global unique index
-- 2) rebuild scoped index in case prior environments created a divergent definition
DROP INDEX IF EXISTS idx_worklog_supersedes_unique;
DROP INDEX IF EXISTS idx_worklog_supersedes_unique_scoped;

-- Create scoped partial unique index
CREATE UNIQUE INDEX IF NOT EXISTS idx_worklog_supersedes_unique_scoped
  ON work_log_entries(workspace_id, instance_id, supersedes_entry_id)
  WHERE supersedes_entry_id IS NOT NULL;

-- Version bump
INSERT OR IGNORE INTO schema_migrations (version, applied_at_utc)
VALUES ('v1.2.1', datetime('now'));
