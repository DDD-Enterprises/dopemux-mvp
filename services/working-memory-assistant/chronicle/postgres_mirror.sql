-- Dope-Memory v1 Postgres Mirror Schema
-- See: docs/spec/dope-memory/v1/03_data_model_postgres.md
--
-- This is the Postgres mirror of the SQLite canonical store.
-- Run this migration to create tables for multi-service access.

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Raw activity events mirror
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

-- Work log entries mirror
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

-- Fast keyword search (tsvector)
ALTER TABLE dm_work_log_entries
  ADD COLUMN IF NOT EXISTS summary_tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('english', coalesce(summary,''))) STORED;

CREATE INDEX IF NOT EXISTS dm_idx_summary_tsv
  ON dm_work_log_entries USING GIN(summary_tsv);

-- Reflection cards mirror (Phase 2)
CREATE TABLE IF NOT EXISTS dm_reflection_cards (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL,
  instance_id TEXT NOT NULL,
  session_id UUID,

  ts TIMESTAMPTZ NOT NULL,

  window_start TIMESTAMPTZ NOT NULL,
  window_end TIMESTAMPTZ NOT NULL,

  trajectory TEXT NOT NULL,

  top_decisions JSONB NOT NULL DEFAULT '[]',
  top_blockers JSONB NOT NULL DEFAULT '[]',
  progress JSONB NOT NULL DEFAULT '{}',
  next_suggested JSONB NOT NULL DEFAULT '[]',

  promotion_candidates JSONB NOT NULL DEFAULT '[]',

  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS dm_ref_idx_ws_ts
  ON dm_reflection_cards(workspace_id, instance_id, ts DESC);

-- Issue links mirror
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

-- Migration tracking
CREATE TABLE IF NOT EXISTS dm_schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO dm_schema_migrations (version)
VALUES ('v1.0.0')
ON CONFLICT (version) DO NOTHING;
