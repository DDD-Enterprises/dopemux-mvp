---
id: dcp-mcp-readonly-connector-policy-contract
title: DCP Connector Policy And Auth Context Contract
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Strict non-secret connector policy schema/loader and provider-neutral authentication context for the DCP read-only facade series.
---

# Connector Policy And Auth Context Contract

Packet: **TP-DCP-MCP-RO-0013**

## Scope

This packet lands **authentication and authorization primitives only**:

- JSON Schema for one connector policy record
- Fail-closed YAML/JSON loader and in-memory store
- Provider-neutral Bearer [REDACTED] against non-secret credential references
- Target and tool authorization from the sealed connector context
- Header stripping/redaction for forgeable connector-identity claims

It does **not** add a public listener, tunnel, ingress middleware wiring, populated
operator credentials, backend adapters, or live provider setup.

## Schema

Canonical schema:

`services/dcp-readonly-facade/schema/connector_policy.schema.json`

Repository example (templates only, all `enabled: false`):

`docs/03-reference/dcp/chatgpt-mcp-readonly/CONNECTOR_POLICY_EXAMPLE.yaml`

Populated operator records must live **outside** the repository (for example under
an operator-owned path referenced by `DCP_FACADE_CONNECTOR_POLICY`).

### Required semantics beyond JSON Schema

| Rule | Behavior |
| --- | --- |
| `default_target_id` | When non-null, must appear in `allowed_target_ids` |
| `multi_target_authorized: false` | At most one allowed target |
| `credential_ref.reference` | Non-secret locator only; secret-like values are rejected |
| `fail_closed.*` | Every key must be `BLOCK` |
| Duplicate `connector_id` | Ambiguous; drop the id entirely |
| `rate_limit.deny_on_backend_unavailable` | Must be `true` |

## Authentication

Module: `dcp_facade.auth_context`

1. Extract a bearer token from `Authorization` or a direct test token.
2. Resolve the connector's `credential_ref` through a secret resolver.
   - Production default: `EnvironmentSecretResolver` for `env:VAR` references only.
   - `os_keychain`, `secret_manager`, `oauth_client`, and `mtls_identity` kinds fail
     closed until a resolver is injected by a later authorized packet.
3. Constant-time compare the resolved secret to the presented token.
4. Deny when the connector is missing, disabled, expired, ambiguous, or unresolved.
5. On success, emit a sealed `ConnectorAuthContext` that **never stores the raw secret**.

Public failure reason is always a generic authentication failure for unknown,
disabled, expired, or wrong-credential cases.

## Authorization

After authentication:

| Check | Result |
| --- | --- |
| `authorize_target` | Allow only targets in `allowed_target_ids` |
| `authorize_tool` | Allow only tools in `allowed_tools` minus `denied_tools` |
| `resolve_request_target` | Use explicit target, else default/single-allowed target |

A context whose seal does not verify is treated as forged and denied.

## Non-forgeable context

- Connector-identity headers (`X-DCP-Connector-Id`, seal headers, etc.) are never
  authoritative. `context_from_untrusted_headers` always denies.
- `strip_untrusted_connector_headers` removes those claims and redacts bearer values.
- Trusted contexts are created only by `authenticate_bearer` and sealed with a
  process-local HMAC key (`DCP_FACADE_AUTH_SEAL_KEY` when set).

## Rotation and revocation

- Credential rotation updates the secret behind the same non-secret reference.
- Old tokens fail after rotation; new tokens succeed.
- Disabling a connector (`enabled: false`) or expiring it revokes access without
  deleting audit labels or fingerprints.

## Deferred to later packets

| Concern | Packet |
| --- | --- |
| Loopback Streamable HTTP ingress + auth-before-discovery | TP-0014 |
| Live ownership verification and safe adapters | TP-0015 |
| Provider setup guides with current commands | TP-0016 |
| Live cross-provider acceptance | TP-0017 |

## Validation commands

```text
uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_connector_policy.py services/dcp-readonly-facade/tests/test_auth_context.py
uv run --frozen pytest -q services/dcp-readonly-facade/tests
uv run --frozen python -m compileall -q services/dcp-readonly-facade/src
```
