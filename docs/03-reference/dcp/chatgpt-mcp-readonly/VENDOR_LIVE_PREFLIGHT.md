---
id: dcp-mcp-readonly-vendor-live-preflight
title: DCP Vendor-Live Acceptance Preflight
type: how-to
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Credential and tool inventory for finishing DCP-ACC-024/025/026 vendor live gates without inventing secrets or opening unauthorized public tunnels.
---

# Vendor-Live Acceptance Preflight

Extends TP-0017 for residual track **vendor-live**.

## What this environment can do without vendor secrets

| Gate | Capability without vendor creds |
| --- | --- |
| DCP-ACC-029 | **PASS** via synthetic two-target isolation |
| DCP-ACC-024/025/026 | **NOT_RUN** with explicit missing inventory |

The harness **never** invents OpenAI/Grok/Gemini credentials and **never** opens a
public quick tunnel automatically (unrestricted public exposure is forbidden).

## Required inventory

### Shared

```text
export DCP_ACCEPTANCE_LIVE=1
export DCP_ACCEPTANCE_LIVE_TOKEN='<connector-bearer-from-secret-store>'
export DCP_ACCEPTANCE_LIVE_PROVIDERS=local,chatgpt,grok,gemini
```

### ChatGPT (DCP-ACC-024)

| Need | Purpose |
| --- | --- |
| `tunnel-client` binary | OpenAI Secure MCP Tunnel |
| `CONTROL_PLANE_API_KEY` | Tunnel runtime API key |
| `OPENAI_TUNNEL_ID` | Tunnel id (never commit) |
| `OPENAI_TUNNEL_PROFILE` | Optional profile name |
| Loopback facade running | `DCP_FACADE_TRANSPORT=streamable-http` on 127.0.0.1 |

### Grok (DCP-ACC-025)

| Need | Purpose |
| --- | --- |
| `PUBLIC_GROK_HOSTNAME` | Stable named HTTPS host |
| Named Cloudflare/ngrok tunnel to loopback facade | Restart-stable route |
| Grok connector bearer | Separate from ChatGPT |

### Gemini (DCP-ACC-026)

| Need | Purpose |
| --- | --- |
| `PUBLIC_GEMINI_HOSTNAME` | Remote MCP URL host |
| Gemini project/API access | Unsupported transport fail-closed proof |

## Commands

```bash
# Preflight inventory (no secrets printed)
uv run --frozen python -c 'from dcp_facade.acceptance import vendor_preflight; import json; print(json.dumps(vendor_preflight(), indent=2))'

# Local + vendor-track (vendor gates stay NOT_RUN until inventory complete)
export DCP_ACCEPTANCE_LIVE=1
export DCP_ACCEPTANCE_LIVE_TOKEN='...'
export DCP_ACCEPTANCE_LIVE_PROVIDERS=local,chatgpt,grok,gemini
PYTHONPATH=services/dcp-readonly-facade/src uv run --frozen python -m dcp_facade.acceptance
```

## Manual vendor receipt attachments (when inventory complete)

For each enabled provider, attach **redacted** evidence under an operator-owned
path (not secrets):

1. Tool discovery export / screenshot (no tokens)
2. Tunnel doctor status (ChatGPT) or DNS/HTTPS check (Grok)
3. Denied-tool and unauthorized-target attempts
4. Credential revoke/retry (old fails, new works)
5. Disconnect/restart proof

Then re-run exact-head readiness with trusted audit.
