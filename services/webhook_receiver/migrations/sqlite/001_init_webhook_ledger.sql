CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS webhook_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_id TEXT,
  received_at_utc TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  headers_json TEXT NOT NULL,
  signature_valid INTEGER NOT NULL DEFAULT 0,
  created_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  UNIQUE(provider, idempotency_key),
  UNIQUE(provider, event_id)
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_provider_received
  ON webhook_events(provider, received_at_utc);

CREATE TABLE IF NOT EXISTS run_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT,
  phase TEXT,
  step_id TEXT,
  partition_id TEXT,
  provider TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_id TEXT,
  provider_ref TEXT,
  webhook_event_id INTEGER,
  dedupe_key TEXT NOT NULL UNIQUE,
  orphaned INTEGER NOT NULL DEFAULT 0,
  created_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  FOREIGN KEY(webhook_event_id) REFERENCES webhook_events(id)
);

CREATE INDEX IF NOT EXISTS idx_run_events_run_created
  ON run_events(run_id, created_at_utc);

CREATE TABLE IF NOT EXISTS async_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL,
  job_kind TEXT NOT NULL,
  external_job_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  phase TEXT NOT NULL,
  step_id TEXT NOT NULL,
  partition_id TEXT NOT NULL,
  attempt INTEGER NOT NULL,
  status TEXT NOT NULL,
  last_error TEXT,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL,
  UNIQUE(provider, external_job_id, attempt)
);

CREATE INDEX IF NOT EXISTS idx_async_jobs_pending
  ON async_jobs(provider, status, updated_at_utc);

CREATE INDEX IF NOT EXISTS idx_async_jobs_tuple
  ON async_jobs(run_id, phase, step_id, partition_id, attempt);
