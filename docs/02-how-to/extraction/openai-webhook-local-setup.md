---
id: openai-webhook-local-setup
title: OpenAI Webhook Local Setup
type: how-to
owner: '@hu3mann'
author: Dopemux Architecture Team
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-21'
status: active
prelude: Configure a local OpenAI webhook receiver with replay support and deterministic ledger verification.
---

# OpenAI Webhook Local Setup

## 1. Start receiver

```bash
docker compose -f /Users/hue/code/dopemux-mvp/compose.yml up -d webhook-receiver
```

## 2. Expose public HTTPS URL

Use either:
- `ngrok http 8790`
- `cloudflared tunnel --url http://localhost:8790`

Configure OpenAI webhook endpoint as:
- `https://<public-host>/webhook/openai`

## 3. Set environment

```bash
export OPENAI_WEBHOOK_SECRET="..."
export OPENAI_API_KEY="..."
```

## 4. Replay fixture event

```bash
python /Users/hue/code/dopemux-mvp/scripts/webhook_replay.py \
  --provider openai \
  --url https://<public-host>/webhook/openai \
  --payload /Users/hue/code/dopemux-mvp/services/webhook_receiver/fixtures/openai_response_completed.json \
  --headers /Users/hue/code/dopemux-mvp/services/webhook_receiver/fixtures/openai_headers.json
```

Replay the same command a second time to verify dedupe.
The replay tool sends payload bytes exactly as stored in `--payload` and prints `payload_sha256`.

## 5. Verify ledger

```bash
sqlite3 /Users/hue/code/dopemux-mvp/.dopemux/webhook_receiver/webhook_receiver.db \
  "select provider, idempotency_key, event_type from webhook_events order by id desc limit 10;"
```
