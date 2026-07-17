---
id: dcp-mcp-readonly-provider-setup
title: DCP Multi-Provider Setup Guide (Placeholders Only)
type: how-to
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Operator setup for ChatGPT, Grok, Gemini, and local Antigravity connectors against the DCP read-only facade using placeholders only.
---

# Provider Setup Guide

**Status:** operator guide for post-0015 series code
**Safety:** placeholders only. Never commit real credentials, tunnel IDs, private
paths, production hostnames, or secret values.

Related contracts:

- [`CONNECTOR_POLICY_CONTRACT.md`](CONNECTOR_POLICY_CONTRACT.md)
- [`CONNECTOR_POLICY_EXAMPLE.yaml`](CONNECTOR_POLICY_EXAMPLE.yaml)
- [`INGRESS_LOOPBACK_CONTRACT.md`](INGRESS_LOOPBACK_CONTRACT.md)
- [`OWNERSHIP_AND_SAFE_ADAPTERS.md`](OWNERSHIP_AND_SAFE_ADAPTERS.md)
- [`DISABLE_AND_ROLLBACK.md`](DISABLE_AND_ROLLBACK.md)
- [`SOURCE_DATE_LEDGER.md`](SOURCE_DATE_LEDGER.md)

## Placeholder legend

| Placeholder | Meaning |
| --- | --- |
| `<REPO_ROOT>` | Dedicated worktree of `DDD-Enterprises/dopemux-mvp` |
| `<TARGET_WORKTREE>` | Worktree exposed by one registry-v2 target |
| `<FACADE_PORT>` | Loopback ingress port |
| `<EXTERNAL_REGISTRY_V2_PATH>` | Operator-owned registry-v2 YAML **outside** the repo |
| `<EXTERNAL_CONNECTOR_POLICY_PATH>` | Operator-owned connector policy YAML **outside** the repo |
| `<CONNECTOR_TOKEN_ENV>` | Env var name holding one connector secret |
| `<PUBLIC_GROK_HOSTNAME>` | Stable public hostname for Grok only |
| `<PUBLIC_GEMINI_HOSTNAME>` | Stable public hostname for Gemini only |
| `<OPENAI_TUNNEL_ID>` | OpenAI tunnel id (never commit) |
| `<OPENAI_TUNNEL_RUNTIME_API_KEY>` | OpenAI tunnel runtime key (never commit) |

## 1. Shared Dopemux preparation

### 1.1 Repo identity

```bash
cd "<REPO_ROOT>"
test -f AGENTS.md
git remote get-url origin
git branch --show-current
git status --short
git rev-parse HEAD
```

Block if origin is not `DDD-Enterprises/dopemux-mvp` or unrelated dirty work is present.

### 1.2 Target worktree MCP sidecars (release-one)

Verified CLI (`uv run --frozen dopemux mcp start --help`):

```bash
uv run --frozen dopemux mcp init
uv run --frozen dopemux mcp repair-config
uv run --frozen dopemux mcp start \
  --repo "<TARGET_WORKTREE>" \
  --services conport,dope-memory \
  --json
uv run --frozen dopemux mcp status --repo "<TARGET_WORKTREE>" --json
uv run --frozen dopemux mcp doctor --repo "<TARGET_WORKTREE>" --json
```

Do **not** start the task orchestrator service for first-release external exposure.

### 1.3 External registry-v2 and connector policy

Create operator files **outside** the repository:

```text
export DCP_FACADE_REGISTRY_V2="<EXTERNAL_REGISTRY_V2_PATH>"
export DCP_FACADE_CONNECTOR_POLICY="<EXTERNAL_CONNECTOR_POLICY_PATH>"
```

- Validate connector records against
  `services/dcp-readonly-facade/schema/connector_policy.schema.json`
- Use repository templates only as templates:
  [`CONNECTOR_POLICY_EXAMPLE.yaml`](CONNECTOR_POLICY_EXAMPLE.yaml) (`examples_only: true`, all `enabled: false`)
- Secrets live in env/keychain/secret manager; policy stores **references** only

### 1.4 Start the loopback facade ingress

Implemented env surface (TP-0014):

```bash
export DCP_FACADE_TRANSPORT=streamable-http
export DCP_FACADE_INGRESS_HOST=127.0.0.1
export DCP_FACADE_INGRESS_PORT="<FACADE_PORT>"
export DCP_FACADE_CONNECTOR_POLICY="<EXTERNAL_CONNECTOR_POLICY_PATH>"
export DCP_FACADE_REGISTRY_V2="<EXTERNAL_REGISTRY_V2_PATH>"

# From services/dcp-readonly-facade with PYTHONPATH including src + repo src:
python -m mcp.server
```

Default transport remains `stdio` when `DCP_FACADE_TRANSPORT` is unset.

### 1.5 Local probes (no provider yet)

```bash
# Health (unauthenticated; no tools)
curl -sS "http://127.0.0.1:<FACADE_PORT>/health"

# Unauthenticated MCP must fail (401, no tool list)
curl -sS -o /tmp/dcp-unauth.json -w "%{http_code}\n" "http://127.0.0.1:<FACADE_PORT>/mcp"

# Authenticated discovery (token from secret store, never committed)
curl -sS "http://127.0.0.1:<FACADE_PORT>/mcp" \
  -H "Authorization: Bearer <VALUE_FROM_SECRET_STORE_NOT_REPO>"
```

Required outcomes:

- listener is loopback only
- unauthenticated discovery fails generically
- authenticated discovery returns only accepted read-only tools
- no write/mutate tool names appear

## 2. ChatGPT (Secure MCP Tunnel)

### Prerequisites

OpenAI Platform tunnel id, runtime API key, eligible workspace permissions, and
web ChatGPT custom MCP app support. Do not store tunnel id or keys in git.

### Local endpoint

```text
http://127.0.0.1:<FACADE_PORT>/mcp
```

Point the tunnel only at the DCP facade, never at ConPort/dope-memory directly.

### Tunnel client shape (verify with current OpenAI docs)

```bash
export CONTROL_PLANE_API_KEY="<OPENAI_TUNNEL_RUNTIME_API_KEY>"
tunnel-client init \
  --sample sample_mcp_stdio_local \
  --profile "<OPENAI_TUNNEL_PROFILE>" \
  --tunnel-id "<OPENAI_TUNNEL_ID>" \
  --mcp-server-url "http://127.0.0.1:<FACADE_PORT>/mcp"
tunnel-client doctor --profile "<OPENAI_TUNNEL_PROFILE>" --explain
tunnel-client run --profile "<OPENAI_TUNNEL_PROFILE>"
```

Re-check official `tunnel-client` help before production use (client may evolve).

### Connector policy binding

```yaml
provider: chatgpt
transport_class: openai_secure_mcp_tunnel
default_target_id: dopemux-main
allowed_target_ids: [dopemux-main]
enabled: false   # flip only after operator approval
```

### Smoke and revoke

1. Discover tools; compare to accepted read-only set.
2. Attempt denied tool and unauthorized target; expect block.
3. Stop tunnel client; confirm no direct backend reachability from the app.
4. Revoke: disable connector record, revoke credential, unlink app, stop tunnel.

## 3. Grok (public Streamable HTTP via tunnel edge)

### Prerequisites

Public HTTPS Streamable HTTP URL. Prefer named Cloudflare tunnel or stable ngrok
domain for acceptance; quick tunnels are ephemeral-only.

### Ephemeral smoke only

```bash
cloudflared tunnel --url "http://127.0.0.1:<FACADE_PORT>"
# or
ngrok http <FACADE_PORT>
```

Stable named tunnel commands must come from current Cloudflare/ngrok docs and
operator config; do not invent DNS or cert steps here.

### Connector creation

1. Create custom Grok connector.
2. Server URL: `https://<PUBLIC_GROK_HOSTNAME>/mcp`
3. Configure Grok-specific bearer credential (separate from ChatGPT).
4. Discover tools; verify read-only allowlist.

### Policy binding

```yaml
provider: grok
transport_class: public_streamable_http
default_target_id: feature-review-a7
allowed_target_ids: [feature-review-a7]
```

## 4. Gemini API / Deep Research

### Prerequisites

Provider account that supports remote MCP URL configuration. Separate credential
and hostname from Grok/ChatGPT.

### Endpoint

```text
https://<PUBLIC_GEMINI_HOSTNAME>/mcp
```

Use Streamable HTTP. Keep `allowed_tools` restricted to release-one reads when
the provider UI supports allowlisting.

### Policy binding

```yaml
provider: gemini_api   # or gemini_deep_research when applicable
transport_class: public_streamable_http
default_target_id: dopemux-main
allowed_target_ids: [dopemux-main]
```

## 5. Local Gemini CLI / Antigravity

Prefer loopback only (no public tunnel):

```text
http://127.0.0.1:<FACADE_PORT>/mcp
```

```yaml
provider: gemini_cli
transport_class: local_streamable_http
```

Never point local agents at backend services directly.

## 6. Cross-provider invariants

1. One connector identity per provider/account class.
2. Independently revocable credentials (rotation invalidates old tokens).
3. Auth before discovery (TP-0014).
4. Ownership verification before any adapter call (TP-0015).
5. Release-one adapter ops only: ConPort decision list/read; dope-memory
   search/replay. Progress, writes, dope-context, and the task orchestrator stay blocked.
6. No real secrets or private paths in repository artifacts.

## 7. Command verification ledger

See [`SOURCE_DATE_LEDGER.md`](SOURCE_DATE_LEDGER.md) for source dates and
[`PROVIDER_COMMAND_LEDGER.md`](PROVIDER_COMMAND_LEDGER.md) for commands verified
against local `--help` in this packet.
