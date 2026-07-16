---
id: TP-DCP-MCP-RO-0014
title: Loopback Streamable HTTP Ingress
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
prelude: Hardened loopback Streamable HTTP ingress with auth-before-discovery for the DCP read-only facade.
last_review: '2026-07-16'
next_review: '2026-10-14'
---
# TP-DCP-MCP-RO-0014

## Objective

Add a loopback-only Streamable HTTP ingress that authenticates connectors
before MCP discovery, enforces rate/concurrency limits, emits redacted audit
events, and supports deterministic start/stop/health.

## Scope

IN:

- Loopback host pin and non-loopback rejection
- ASGI auth middleware over MCP paths
- Rate/concurrency limits from connector policy
- Structured redacted audit log
- Server lifecycle + docs/tests/packet/proof
- Optional `DCP_FACADE_TRANSPORT=streamable-http` wiring (stdio remains default)

OUT:

- Public binds, tunnels, provider setup, real credentials, backend adapters,
  ownership probes, compose exposure, CI auditor routing changes

## Validation

```text
uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_ingress.py services/dcp-readonly-facade/tests/test_loopback_server.py
uv run --frozen pytest -q services/dcp-readonly-facade/tests
uv run --frozen python -m compileall -q services/dcp-readonly-facade/src
uv run --frozen python -m jsonschema -i task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0014.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
git diff --check
```

## Stop Conditions

- Implementation requires a non-loopback default bind or tunnel creation
- Unauthenticated clients can list tools
- Diff escapes the packet allowlist
- Trusted audit is claimed from local AGY alone

## Rollback

Revert the TP-0014 commits and keep `DCP_FACADE_TRANSPORT=stdio`. No backend
change is required.
