# webhook_receiver

OpenAI webhook sidecar for Dopemux.

## Endpoint

- `POST /webhook/openai`
- `GET /healthz`

## Environment

- `OPENAI_WEBHOOK_SECRET` (required)
- `OPENAI_API_KEY` (required by SDK init; can be non-privileged)
- `WEBHOOK_RECEIVER_HOST` (default `0.0.0.0`)
- `WEBHOOK_RECEIVER_PORT` (default `8790`)
- `WEBHOOK_DB_PATH` (default `/data/webhook_receiver.db`)

## Behavior

- Verifies signatures via OpenAI SDK webhook unwrap on raw body.
- Deduplicates deliveries by `webhook-id`.
- Stores raw webhook events and normalized run-event rows in sqlite.
- Returns fast `204` on accepted or duplicate deliveries.
