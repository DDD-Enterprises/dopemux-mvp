-- Dope-Memory v1 SQLite Canonical Schema
-- See: docs/spec/dope-memory/v1/02_data_model_sqlite.md

-- 1) Raw events (7-day retention)
CREATE TABLE IF NOT EXISTS raw_activity_events (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,
  session_id TEXT,

  ts_utc TEXT NOT NULL,
  event_type TEXT NOT NULL,
  source TEXT NOT NULL,

  payload_json TEXT NOT NULL,
  redaction_level TEXT NOT NULL DEFAULT 'strict',

  ttl_days INTEGER NOT NULL DEFAULT 7,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_events_ws_ts
  ON raw_activity_events(workspace_id, instance_id, ts_utc DESC);

CREATE INDEX IF NOT EXISTS idx_raw_events_type_ts
  ON raw_activity_events(event_type, ts_utc DESC);

-- 2) Curated work log entries (durable)
CREATE TABLE IF NOT EXISTS work_log_entries (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,
  session_id TEXT,

  ts_utc TEXT NOT NULL,
  duration_sec INTEGER,

  category TEXT NOT NULL CHECK (category IN (
    'planning', 'implementation', 'review', 'debugging',
    'research', 'deployment', 'architecture', 'documentation'
  )),
  entry_type TEXT NOT NULL CHECK (entry_type IN (
    'decision', 'blocker', 'resolution', 'milestone', 'error',
    'workflow_transition', 'manual_note', 'task_event'
  )),
  workflow_phase TEXT CHECK (workflow_phase IN (
    'planning', 'implementation', 'review', 'audit', 'deployment', 'maintenance'
  ) OR workflow_phase IS NULL),

  summary TEXT NOT NULL,
  details_json TEXT,
  reasoning TEXT,

  outcome TEXT NOT NULL DEFAULT 'in_progress' CHECK (outcome IN (
    'success', 'partial', 'blocked', 'abandoned', 'in_progress', 'failed'
  )),
  importance_score INTEGER NOT NULL DEFAULT 5 CHECK (importance_score BETWEEN 1 AND 10),

  tags_json TEXT NOT NULL DEFAULT '[]',

  linked_decisions_json TEXT,
  linked_files_json TEXT,
  linked_commits_json TEXT,
  linked_chat_range_json TEXT,

  parent_entry_id TEXT,

  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_worklog_ws_ts
  ON work_log_entries(workspace_id, instance_id, ts_utc DESC);

CREATE INDEX IF NOT EXISTS idx_worklog_cat_type
  ON work_log_entries(category, entry_type);

CREATE INDEX IF NOT EXISTS idx_worklog_phase
  ON work_log_entries(workflow_phase);

CREATE INDEX IF NOT EXISTS idx_worklog_importance
  ON work_log_entries(importance_score DESC, ts_utc DESC);

-- 3) Issue links
CREATE TABLE IF NOT EXISTS issue_links (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,

  issue_entry_id TEXT NOT NULL,
  resolution_entry_id TEXT NOT NULL,

  confidence REAL NOT NULL DEFAULT 0.7,
  evidence_window_min INTEGER NOT NULL DEFAULT 30,

  created_at_utc TEXT NOT NULL,

  FOREIGN KEY (issue_entry_id) REFERENCES work_log_entries(id),
  FOREIGN KEY (resolution_entry_id) REFERENCES work_log_entries(id)
);

CREATE INDEX IF NOT EXISTS idx_issue_links_issue
  ON issue_links(issue_entry_id);

CREATE INDEX IF NOT EXISTS idx_issue_links_resolution
  ON issue_links(resolution_entry_id);

-- 4) Reflection cards (Phase 2, created now for forward compatibility)
CREATE TABLE IF NOT EXISTS reflection_cards (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,
  session_id TEXT,

  ts_utc TEXT NOT NULL,

  window_start_utc TEXT NOT NULL,
  window_end_utc TEXT NOT NULL,

  trajectory TEXT NOT NULL,
  top_decisions_json TEXT NOT NULL DEFAULT '[]',
  top_blockers_json TEXT NOT NULL DEFAULT '[]',
  progress_json TEXT NOT NULL DEFAULT '{}',
  next_suggested_json TEXT NOT NULL DEFAULT '[]',

  promotion_candidates_json TEXT NOT NULL DEFAULT '[]',
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reflection_ws_ts
  ON reflection_cards(workspace_id, instance_id, ts_utc DESC);

-- 5) Trajectory state (Phase 2, created now for forward compatibility)
CREATE TABLE IF NOT EXISTS trajectory_state (
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,
  session_id TEXT,

  updated_at_utc TEXT NOT NULL,

  current_stream TEXT NOT NULL DEFAULT '',
  current_goal_json TEXT NOT NULL DEFAULT '{}',
  last_steps_json TEXT NOT NULL DEFAULT '[]',

  PRIMARY KEY (workspace_id, instance_id)
);

-- Migration tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at_utc TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_migrations (version, applied_at_utc)
VALUES ('v1.0.0', datetime('now'));
