---
id: webhooks
title: Dopemux Webhooks
type: how-to
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-10-10'
last_review: '2026-10-10'
next_review: '2027-04-10'
prelude: Configure and verify the Cloudflare Tunnel and webhook receiver for Dopemux; relocated from the repository root in consolidation W5.
---
# Dopemux Webhooks

This document describes how to configure and verify the Cloudflare Tunnel and Webhook Receiver for Dopemux.

## 1. Cloudflare DNS Routing (One-Time Setup)

You must route your DNS to the local tunnel:
```bash
cloudflared tunnel route dns dopemux-webhooks webhooks.krohman.org
```

## 2. Run Cloudflared Permanently

We use a macOS launchd daemon to keep `cloudflared` running in the background without an open terminal session.

```bash
./ops/cloudflared/install_macos_launchd.sh
```

To stop or uninstall the daemon:
```bash
./ops/cloudflared/uninstall_macos_launchd.sh
```

## 3. Start Webhook Receiver

The receiver is managed by Docker Compose. You can start it and tail its logs with:
```bash
make webhook-up
make webhook-logs
```

## 4. Confirm URLs

Verify both local and public health endpoints:
```bash
make webhook-health
```
Alternatively:
```bash
curl -fsS http://localhost:8790/healthz
curl -fsS https://webhooks.krohman.org/healthz
```

## 5. Register Webhook in OpenAI Dashboard

**Endpoint URL**:
- `https://webhooks.krohman.org/webhook/openai`

**Webhook Secret**:
- Store the generated secret as `OPENAI_WEBHOOK_SECRET` in your `.env` file used by compose.

## 6. Smoke Tests & Verification

We provide an automated smoke test that verifies health, tests a simulated OpenAI payload, and outputs deduplication and database metrics.

```bash
make webhook-smoke
```
