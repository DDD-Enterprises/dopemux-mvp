---
id: TP-DCP-MCP-RO-0013
title: Connector Policy Schema And Auth Context
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
prelude: Strict connector policy schema/loader and provider-neutral authentication context for the DCP read-only multi-provider series.
last_review: '2026-07-16'
next_review: '2026-10-14'
---
# TP-DCP-MCP-RO-0013

## Objective

Implement the connector policy contract and provider-neutral authentication
context so later ingress can authorize independently revocable connectors
before target resolution and tool dispatch.

## Scope

IN:

- Connector policy JSON Schema and fail-closed loader/store.
- Bearer [REDACTED] against non-secret credential references.
- Sealed connector auth context; target/tool authorization.
- Header stripping/redaction for forgeable connector claims.
- Contract docs, redacted examples, tests, packet, proof.

OUT:

- Public listeners, tunnels, provider setup, real credentials, backend
  adapters, ownership probes, compose/CI auditor routing, populated operator
  policy files.

## Invariants

- Raw secrets never enter the repository, policy documents, or sealed context.
- Auth failures stay generic across missing/disabled/expired/wrong identity.
- Connector-identity headers are never trusted as authentication.
- Deny-by-default for targets and tools outside the connector allowlists.
- No public ingress or live backend/provider action in this packet.

## Validation

```text
uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_connector_policy.py services/dcp-readonly-facade/tests/test_auth_context.py
uv run --frozen pytest -q services/dcp-readonly-facade/tests
uv run --frozen python -m compileall -q services/dcp-readonly-facade/src
uv run --frozen python -m jsonschema -i task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0013.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
git diff --check
```

## Stop Conditions

- Implementation requires a public bind, tunnel, or real provider credential.
- Diff includes files outside the packet allowlist.
- Auth context can be forged from headers or retains raw secrets.
- Trusted embedded audit is claimed from local AGY evidence.

## Rollback

Revert the TP-0013 commit stack. Auth primitives are unused by the public
FastMCP server in this packet, so rollback does not change live exposure.
