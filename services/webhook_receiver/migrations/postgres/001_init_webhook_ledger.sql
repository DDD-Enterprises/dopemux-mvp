CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at_utc TIMESTAMPTZ NOT NULL DEFAULT (now() at time zone 'utc')
);

CREATE TABLE IF NOT EXISTS webhook_events (
  id BIGSERIAL PRIMARY KEY,
  provider TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_id TEXT,
  received_at_utc TIMESTAMPTZ NOT NULL,
  payload_json JSONB NOT NULL,
  headers_json JSONB NOT NULL,
  signature_valid BOOLEAN NOT NULL DEFAULT FALSE,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT (now() at time zone 'utc'),
  UNIQUE(provider, idempotency_key)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_webhook_events_provider_event_id
  ON webhook_events(provider, event_id)
  WHERE event_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_webhook_events_provider_received
  ON webhook_events(provider, received_at_utc);

CREATE TABLE IF NOT EXISTS run_events (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT,
  phase TEXT,
  step_id TEXT,
  partition_id TEXT,
  provider TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_id TEXT,
  provider_ref TEXT,
  webhook_event_id BIGINT REFERENCES webhook_events(id),
  dedupe_key TEXT NOT NULL UNIQUE,
  orphaned BOOLEAN NOT NULL DEFAULT FALSE,
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT (now() at time zone 'utc')
);

CREATE INDEX IF NOT EXISTS idx_run_events_run_created
  ON run_events(run_id, created_at_utc);

CREATE TABLE IF NOT EXISTS async_jobs (
  id BIGSERIAL PRIMARY KEY,
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
  created_at_utc TIMESTAMPTZ NOT NULL DEFAULT (now() at time zone 'utc'),
  updated_at_utc TIMESTAMPTZ NOT NULL DEFAULT (now() at time zone 'utc'),
  UNIQUE(provider, external_job_id, attempt)
);

CREATE INDEX IF NOT EXISTS idx_async_jobs_pending
  ON async_jobs(provider, status, updated_at_utc);

CREATE INDEX IF NOT EXISTS idx_async_jobs_tuple
  ON async_jobs(run_id, phase, step_id, partition_id, attempt);
