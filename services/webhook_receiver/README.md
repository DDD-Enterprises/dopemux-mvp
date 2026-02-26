# webhook_receiver

OpenAI-first webhook sidecar with provider-agnostic event ledger and poller adapters.

## Endpoints

- `POST /webhook/openai`
- `GET /healthz`

## Environment

- `OPENAI_WEBHOOK_SECRET` (required for webhook verification)
- `OPENAI_API_KEY` (required by OpenAI SDK init)
- `WEBHOOK_RECEIVER_HOST` (default `0.0.0.0`)
- `WEBHOOK_RECEIVER_PORT` (default `8790`)
- `WEBHOOK_DB_URL` (`sqlite:////...` or `postgresql://...`; preferred)
- `WEBHOOK_DB_PATH` (legacy SQLite fallback, default `/data/webhook_receiver.db`)

## Ledger Tables

- `provider_events`
  - Unique `(provider, delivery_id)` and unique `dedupe_key`
- `run_events`
  - Normalized event rows linked to provider events with unique `dedupe_key`
  - Includes `orphaned=1` when event attempt is stale vs latest async job attempt
- `async_jobs`
  - Async job registry keyed by `(provider, external_job_id, attempt)`
- `webhook_events` (legacy compatibility fallback)

## Behavior

- Verifies OpenAI signatures with SDK `webhooks.unwrap` on raw request body.
- Deduplicates OpenAI deliveries by `webhook-id`.
- Returns fast `204` for accepted and duplicate events.
- Writes normalized rows into `provider_events` and `run_events`.

## Poller Mode

Poller adapters for `xai` and `gemini` are available through:

```bash
python /app/services/webhook_receiver/poller.py --providers xai,gemini --once
```

The poller reads `async_jobs` in `submitted/running`, emits normalized completion/failure events idempotently, and updates job status.
