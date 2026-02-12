-- Packet G: Scope Supersession Unique Index
-- Version: v1.2.1
-- Purpose: Scope supersession uniqueness to workspace and instance to prevent cross-workspace contamination.

-- Drop old global index
DROP INDEX IF EXISTS idx_worklog_supersedes_unique;

-- Create new scoped index
CREATE UNIQUE INDEX IF NOT EXISTS idx_worklog_supersedes_unique_scoped
  ON work_log_entries(workspace_id, instance_id, supersedes_entry_id)
  WHERE supersedes_entry_id IS NOT NULL;

-- Version bump
INSERT OR IGNORE INTO schema_migrations (version, applied_at_utc)
VALUES ('v1.2.1', datetime('now'));
