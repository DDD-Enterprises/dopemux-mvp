---
id: dopemux-hooksd
title: Dopemux Hooksd
type: reference
owner: '@hu3mann'
last_review: '2026-04-18'
next_review: '2026-07-18'
author: '@codex'
date: '2026-04-18'
prelude: Reference for the current Dopemux hook-facing runtime surfaces. This checkout does not contain a first-class `hooksd` service name; the closest verified operator runtime is the `webhook-receiver` sidecar plus the separate local `native-hooks` Claude adapter.
---
# Dopemux Hooksd

## Runtime role

There is no verified runtime entrypoint named `hooksd` in this checkout.

The closest active operator surface is the webhook sidecar:

- `services/webhook_receiver/server.py`
- `services/webhook_receiver/poller.py`
- `compose.yml` services `webhook-receiver` and `webhook-poller`

Separate from that HTTP sidecar, Dopemux also contains a local Claude hook adapter:

- `src/dopemux/claude/native_hooks.py`
- CLI registration surface: `src/dopemux/cli.py` `dopemux native-hooks register`

These are distinct surfaces with different authority and transport:

- `webhook-receiver` is an HTTP integration sidecar with a durable event ledger.
- `native-hooks` is a local process hook for Claude Code workflow continuity.

This document keeps the user-requested `hooksd` label for discoverability, but it does not claim that `hooksd` is a canonical runtime name.

## Verified HTTP hook surfaces

The webhook sidecar exposes:

- `POST /webhook/openai`
- `GET /healthz`

Observed behavior from `services/webhook_receiver/server.py`:

- accepts only `/webhook/openai`
- requires `OPENAI_WEBHOOK_SECRET` at request time
- refuses startup in `DPMX_ENV=prod` when `OPENAI_WEBHOOK_SECRET` is missing
- verifies signatures through `OpenAI().webhooks.unwrap(...)`
- requires a delivery id header such as `webhook-id`
- returns `204 No Content` for accepted and duplicate deliveries
- writes accepted events into the ledger before returning success

The health route returns JSON with:

- `status: ok`
- `schema: DPMX_WEBHOOK_V2`

## Verified compose and operator wiring

The active compose-defined services are:

- `webhook-receiver`
- `webhook-poller`

Observed defaults from `compose.yml`:

- receiver port mapping `8790:8790`
- shared ledger volume `./.dopemux/webhook_receiver:/data`
- receiver command comes from `services/webhook_receiver/Dockerfile`
- poller command is `python /app/services/webhook_receiver/poller.py --providers xai,gemini --interval-seconds 10`

Observed helper targets from `Makefile`:

- `make webhook-up`
- `make webhook-down`
- `make webhook-logs`
- `make webhook-smoke`
- `make webhook-health`
- `make webhook-db-stats`
- `make webhook-db-tail`
- `make webhook-db-tail-run`
- `make webhook-proof`

## Ledger and storage boundary

The canonical writer abstraction for webhook persistence is the event store interface in:

- `services/webhook_receiver/ledger/interface.py`

Observed write classes:

- `WebhookEventInsert`
- `RunEventInsert`
- `AsyncJobInsert`

Observed storage backends:

- SQLite
- PostgreSQL

Database resolution in `services/webhook_receiver/storage.py` is:

1. `WEBHOOK_DB_URL` if set
2. `WEBHOOK_DB_PATH` if set
3. `/data/webhook_receiver.db` when the container data directory is writable
4. local fallback `.dopemux/webhook_receiver/webhook_receiver.db`

The service README and admin CLI describe these ledger tables:

- `webhook_events` as the legacy compatibility table name used by the admin CLI
- `run_events`
- `async_jobs`

The README also refers to `provider_events`. In the current admin CLI implementation, `provider_events` is presented as a compatibility label that maps to `webhook_events`.

## Poller scope

The background poller in `services/webhook_receiver/poller.py` is not a generic hook daemon. It has a narrower verified role:

- supports only `xai` and `gemini`
- rejects unsupported provider ids fail-closed
- scans pending async jobs from the shared ledger
- emits normalized `job.completed` or `job.failed` events
- marks stale attempts as `orphaned`

Supported terminal statuses are currently:

- `completed`
- `failed`

## Local native hook surface

The `native-hooks` CLI registration path in `src/dopemux/cli.py` installs a command hook pointing at:

- `src/dopemux/claude/native_hooks.py`

Observed Claude hook events handled by that adapter include:

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PermissionRequest`
- `PostToolUse`
- `PostToolUseFailure`
- `Stop`
- `SubagentStop`
- `PreCompact`
- `SessionEnd`

Observed responsibilities in `src/dopemux/claude/native_hooks.py`:

- inject workflow context into Claude sessions
- record hook history through the workflow kernel
- block tool use when workflow time or iteration gates are exceeded
- block stop events when workflow continuity rules require it

This local adapter is hook-related, but it is not served by the webhook sidecar and does not share the same transport contract.

## Known drift and unresolved naming

- No inspected runtime file, compose service, or CLI group uses the exact name `hooksd`.
- `SERVICE_CATALOG.md` classifies `webhook-receiver` as a support-sidecar service, not a canonical architecture spine component.
- `Makefile` uses `webhook_receiver` in docker compose commands, while `compose.yml` defines `webhook-receiver`. This naming mismatch is present in the current checkout and should be treated as drift until verified otherwise.
- The truth-pack paths named in repo-level instructions were not present in this checkout, so this page is grounded in runtime code, compose wiring, `SERVICE_CATALOG.md`, and the local service README rather than an extracted truth bundle.

## Related docs

- `docs/02-how-to/extraction/openai-webhook-local-setup.md`
- `README_WEBHOOKS.md`
- `services/webhook_receiver/README.md`
- `docs/03-reference/services/server-registry.md`
