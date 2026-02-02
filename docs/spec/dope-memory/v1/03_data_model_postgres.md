---
id: 03_data_model_postgres
title: 03_Data_Model_Postgres
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Dope-Memory v1 — Postgres Mirror Data Model

Postgres provides fast querying and shared access across services.
SQLite remains canonical for Dope-Memory.

## Tables

### dm_raw_activity_events

```sql
CREATE TABLE IF NOT EXISTS dm_raw_activity_events (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL,
  instance_id TEXT NOT NULL,
  session_id UUID,

  ts TIMESTAMPTZ NOT NULL,
  event_type TEXT NOT NULL,
  source TEXT NOT NULL,

  payload JSONB NOT NULL,
  redaction_level TEXT NOT NULL DEFAULT 'strict',

  ttl_days INT NOT NULL DEFAULT 7,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS dm_raw_idx_ws_ts
  ON dm_raw_activity_events(workspace_id, instance_id, ts DESC);

CREATE INDEX IF NOT EXISTS dm_raw_idx_type_ts
  ON dm_raw_activity_events(event_type, ts DESC);
```

### dm_work_log_entries

```sql
CREATE TABLE IF NOT EXISTS dm_work_log_entries (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL,
  instance_id TEXT NOT NULL,
  session_id UUID,

  ts TIMESTAMPTZ NOT NULL,
  duration_seconds INT,

  category TEXT NOT NULL,
  entry_type TEXT NOT NULL,
  workflow_phase TEXT,

  summary TEXT NOT NULL,
  details JSONB,
  reasoning TEXT,

  outcome TEXT NOT NULL DEFAULT 'in_progress',
  importance_score SMALLINT NOT NULL DEFAULT 5 CHECK (importance_score BETWEEN 1 AND 10),

  tags TEXT[] NOT NULL DEFAULT '{}',

  linked_decisions UUID[],
  linked_files JSONB,
  linked_commits TEXT[],
  linked_chat_range JSONB,

  parent_entry_id UUID,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS dm_idx_ws_ts
  ON dm_work_log_entries(workspace_id, instance_id, ts DESC);

CREATE INDEX IF NOT EXISTS dm_idx_cat_type
  ON dm_work_log_entries(category, entry_type);

CREATE INDEX IF NOT EXISTS dm_idx_phase
  ON dm_work_log_entries(workflow_phase);

CREATE INDEX IF NOT EXISTS dm_idx_tags_gin
  ON dm_work_log_entries USING GIN(tags);

CREATE INDEX IF NOT EXISTS dm_idx_files_gin
  ON dm_work_log_entries USING GIN(linked_files);

-- Fast keyword search (Phase 1)
ALTER TABLE dm_work_log_entries
  ADD COLUMN IF NOT EXISTS summary_tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('english', coalesce(summary,''))) STORED;

CREATE INDEX IF NOT EXISTS dm_idx_summary_tsv
  ON dm_work_log_entries USING GIN(summary_tsv);
```

### dm_reflection_cards (Phase 2)

```sql
CREATE TABLE IF NOT EXISTS dm_reflection_cards (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL,
  instance_id TEXT NOT NULL,
  session_id UUID,

  ts TIMESTAMPTZ NOT NULL,

  window_start TIMESTAMPTZ NOT NULL,
  window_end TIMESTAMPTZ NOT NULL,

  trajectory TEXT NOT NULL,

  top_decisions JSONB NOT NULL,
  top_blockers JSONB NOT NULL,
  progress JSONB NOT NULL,
  next_suggested JSONB NOT NULL,

  promotion_candidates JSONB NOT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS dm_ref_idx_ws_ts
  ON dm_reflection_cards(workspace_id, instance_id, ts DESC);
```

### dm_issue_links

```sql
CREATE TABLE IF NOT EXISTS dm_issue_links (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL,
  instance_id TEXT NOT NULL,

  issue_entry_id UUID NOT NULL,
  resolution_entry_id UUID NOT NULL,

  confidence REAL NOT NULL DEFAULT 0.7,
  evidence_window_min INT NOT NULL DEFAULT 30,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS dm_issue_idx_issue
  ON dm_issue_links(issue_entry_id);

CREATE INDEX IF NOT EXISTS dm_issue_idx_resolution
  ON dm_issue_links(resolution_entry_id);
```

## Mirroring Rules
- Upserts keyed by id.
- updated_at must be set on changes.
- Mirror worker must be idempotent: reprocessing same SQLite rows must not create duplicates.
- If workspace_id/session_id mappings are not yet UUIDs in your system, store as TEXT in Phase 1 mirror and migrate later. Prefer UUID now if already present.
