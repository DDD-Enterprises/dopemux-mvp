---
id: 02_data_model_sqlite
title: 02_Data_Model_Sqlite
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: 02_Data_Model_Sqlite (explanation) for dopemux documentation and developer
  workflows.
---
# Dope-Memory v1 — SQLite Canonical Data Model

SQLite is canonical for the Chronicle store. Postgres is a mirror.

All timestamps stored as UTC ISO8601 strings (e.g., "2026-02-02T10:15:30Z").

## Tables

### 1) raw_activity_events
- Short retention
- Contains redacted payloads
- Used for correlation windows and later summarization context

```sql
CREATE TABLE IF NOT EXISTS raw_activity_events (
  id TEXT PRIMARY KEY,                       -- uuid
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,
  session_id TEXT,

  ts_utc TEXT NOT NULL,                      -- ISO8601 UTC
  event_type TEXT NOT NULL,                  -- taxonomy
  source TEXT NOT NULL,                      -- producer identity

  payload_json TEXT NOT NULL,                -- redacted JSON string
  redaction_level TEXT NOT NULL DEFAULT 'strict',

  ttl_days INTEGER NOT NULL DEFAULT 7,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_events_ws_ts
  ON raw_activity_events(workspace_id, instance_id, ts_utc DESC);

CREATE INDEX IF NOT EXISTS idx_raw_events_type_ts
  ON raw_activity_events(event_type, ts_utc DESC);
```

### 2) work_log_entries

Curated chronicle entries.

```sql
CREATE TABLE IF NOT EXISTS work_log_entries (
  id TEXT PRIMARY KEY,                       -- uuid
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,
  session_id TEXT,

  ts_utc TEXT NOT NULL,
  duration_sec INTEGER,

  category TEXT NOT NULL,                    -- planning|implementation|review|debugging|research|deployment|architecture|documentation
  entry_type TEXT NOT NULL,                  -- decision|blocker|resolution|milestone|error|workflow_transition|manual_note|task_event
  workflow_phase TEXT,                       -- planning|implementation|review|audit|deployment|maintenance

  summary TEXT NOT NULL,
  details_json TEXT,                         -- redacted JSON
  reasoning TEXT,

  outcome TEXT NOT NULL DEFAULT 'in_progress', -- success|partial|blocked|abandoned|in_progress|failed
  importance_score INTEGER NOT NULL DEFAULT 5, -- 1..10

  tags_json TEXT NOT NULL DEFAULT '[]',       -- JSON array of strings

  linked_decisions_json TEXT,                -- JSON array of ids (string form)
  linked_files_json TEXT,                    -- JSON array [{path, action, stats?}]
  linked_commits_json TEXT,                  -- JSON array [sha...]
  linked_chat_range_json TEXT,               -- JSON object {turn_start, turn_end} or {source, pointer}

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
```

### 3) reflection_cards (Phase 2)

```sql
CREATE TABLE IF NOT EXISTS reflection_cards (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,
  session_id TEXT,

  ts_utc TEXT NOT NULL,

  window_start_utc TEXT NOT NULL,
  window_end_utc TEXT NOT NULL,

  trajectory TEXT NOT NULL,                  -- 1 sentence
  top_decisions_json TEXT NOT NULL,          -- JSON array (top 3)
  top_blockers_json TEXT NOT NULL,           -- JSON array (top 3)
  progress_json TEXT NOT NULL,               -- JSON
  next_suggested_json TEXT NOT NULL,         -- JSON array (1-3)

  promotion_candidates_json TEXT NOT NULL,   -- JSON array of curated entry ids
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reflection_ws_ts
  ON reflection_cards(workspace_id, instance_id, ts_utc DESC);
```

### 4) issue_links

```sql
CREATE TABLE IF NOT EXISTS issue_links (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,

  issue_entry_id TEXT NOT NULL,
  resolution_entry_id TEXT NOT NULL,

  confidence REAL NOT NULL DEFAULT 0.7,
  evidence_window_min INTEGER NOT NULL DEFAULT 30,

  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_issue_links_issue
  ON issue_links(issue_entry_id);

CREATE INDEX IF NOT EXISTS idx_issue_links_resolution
  ON issue_links(resolution_entry_id);
```

### 5) trajectory_state (Phase 2+)

Stores current stream and last steps for trajectory-aware boosting.

```sql
CREATE TABLE IF NOT EXISTS trajectory_state (
  workspace_id TEXT NOT NULL,
  instance_id TEXT NOT NULL,
  session_id TEXT,

  updated_at_utc TEXT NOT NULL,

  current_stream TEXT NOT NULL,              -- e.g. "auth", "db", "ci"
  current_goal_json TEXT NOT NULL,           -- JSON: {id, title, source}
  last_steps_json TEXT NOT NULL,             -- JSON array of last 3 entry ids

  PRIMARY KEY (workspace_id, instance_id)
);
```

## Retention Job (Raw Events)

A periodic cleanup must delete raw events older than ttl_days:
- Compute cutoff = now_utc - ttl_days
- Delete raw_activity_events where ts_utc < cutoff
