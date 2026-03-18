---
id: TP-CLOUDFLARE-WEBHOOKS-0001
title: Tp Cloudflare Webhooks 0001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Tp Cloudflare Webhooks 0001 (explanation) for dopemux documentation and developer
  workflows.
---
# TP-CLOUDFLARE-WEBHOOKS-0001: Cloudflare Tunnel Option B — Automated, Locked Down, Proof-Pack Ready (+ OpenAI Checklist)

## Objective
Turn your current “works on my machine” Cloudflare tunnel + webhook receiver into a repeatable, hardened, automated setup.

## Scope
- Cloudflared tunnel automation (local dev + “always-on” host)
- Cloudflare-side restrictions (Access/WAF where appropriate)
- Receiver-side hardening (signature verify required, fast-ack, dedupe)
- Compose wiring + env management + health/proof tooling
- Proof-pack CLI outputs

## Implementation Plan
1. **Commit 1**: Versioned cloudflared config + deterministic bootstrap scripts
2. **Commit 2**: Compose hardening + env + health + DB access (`db_inspect.py`)
3. **Commit 3**: Cloudflare edge lockdown (minimum viable, sane defaults)
4. **Commit 4**: Receiver lock-down (strict routing, strict header requirements, minimal logging)
5. **Commit 5**: Automate cloudflared as a daemon via macOS LaunchAgent
6. **Commit 6**: One-command “Operator Proof Pack” script

## Acceptance Criteria
- `https://webhooks.krohman.org/healthz` returns 200
- `POST https://webhooks.krohman.org/webhook/openai` accepts valid signed events and 204s quickly
- Invalid signature returns 401, missing webhook-id returns 400
- Duplicate delivery id does not create second insert
- Cloudflared auto-restarts on reboot/login via LaunchAgent
- Single script produces proof pack
