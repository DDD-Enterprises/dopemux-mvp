---
id: dcp-mcp-readonly-ingress-loopback-contract
title: DCP Loopback Streamable HTTP Ingress Contract
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Hardened loopback Streamable HTTP ingress with auth-before-discovery, rate limits, redacted audit, and start/stop/health for the DCP read-only facade.
---

# Loopback Streamable HTTP Ingress Contract

Packet: **TP-DCP-MCP-RO-0014**

## Scope

This packet adds a **loopback-only** authenticated ingress in front of the facade
MCP surface:

- Pin bind host to `127.0.0.1` / loopback (reject `0.0.0.0` and LAN hosts)
- Authenticate connector policy credentials **before** MCP discovery/dispatch
- Per-connector rate and concurrency limits
- Structured redacted audit events
- Deterministic start / stop / health

It does **not** create tunnels, public binds, provider credentials, backend
adapters, or compose exposure defaults.

## Modules

| Module | Role |
| --- | --- |
| `dcp_facade.ingress` | ASGI auth middleware + protected MCP placeholder app |
| `dcp_facade.loopback_server` | Loopback bind, uvicorn lifecycle, env wiring |
| `dcp_facade.rate_limit` | Per-connector token bucket + concurrency |
| `dcp_facade.ingress_audit` | Bounded redacted audit log |

Depends on TP-0013: `connector_policy` + `auth_context`.

## Transport selection

| `DCP_FACADE_TRANSPORT` | Behavior |
| --- | --- |
| `stdio` (default) | Existing FastMCP stdio path; no listener |
| `streamable-http` / `http` / `loopback-http` | Loopback ingress on `DCP_FACADE_INGRESS_HOST`:`DCP_FACADE_INGRESS_PORT` |

Environment:

```text
DCP_FACADE_INGRESS_HOST=127.0.0.1   # required loopback
DCP_FACADE_INGRESS_PORT=8765       # or 0 for ephemeral in tests
DCP_FACADE_CONNECTOR_POLICY=/path/to/operator-policy.yaml
```

## Routes

| Path | Auth | Behavior |
| --- | --- | --- |
| `/health`, `/healthz` | no | Liveness only; never lists tools |
| `/mcp` (+ prefixes) | **required** | Discovery/dispatch only after sealed connector auth |
| other non-health | **required** | Fail closed (no bypass surface) |

Unauthenticated MCP requests return HTTP 401 with a generic authentication
error and **no tool manifest**.

## Rate limits

After successful authentication, the connector's policy `rate_limit` applies:

- `requests_per_minute` + `burst` (token bucket)
- `max_concurrent` in-flight requests

Exceeded limits return HTTP 429 without reflecting secrets or topology.

## Audit

Each decision records: timestamp, decision, path, method, connector_id (when
known), credential fingerprint, status, generic reason, redaction categories.
Raw bearer tokens never appear in audit dumps.

## FastMCP coupling

When FastMCP is installed and exposes an HTTP app factory, the loopback server
attempts to wrap it. When FastMCP is absent (test/constrained envs), an
authenticated placeholder MCP app serves a minimal tools list for contract tests.
Either way, auth middleware remains outside the inner app.

## Validation commands

```text
uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_ingress.py services/dcp-readonly-facade/tests/test_loopback_server.py
uv run --frozen pytest -q services/dcp-readonly-facade/tests
uv run --frozen python -m compileall -q services/dcp-readonly-facade/src
```
