---
id: dcp-mcp-readonly-disable-and-rollback
title: DCP Connector Disable And Rollback Guide
type: how-to
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Operator steps to disable connectors, revoke credentials, stop tunnels, and roll back the DCP read-only facade without mutating backends.
---

# Disable And Rollback Guide

Use this guide when a provider smoke fails, an unexpected tool appears, or an
operator wants to retire exposure. **Backend data remains unchanged.**

## Immediate stop (ordered)

1. **Disable connector policy records** outside the repo
   Set `enabled: false` on each connector record under
   `DCP_FACADE_CONNECTOR_POLICY`. Reload/restart the facade process so auth fails closed.
2. **Revoke connector secrets**
   Rotate or delete the secret behind each `credential_ref` (env/keychain/secret manager).
   Old tokens must fail authentication after rotation (TP-0013).
3. **Stop provider tunnels / apps**
   - ChatGPT: stop `tunnel-client`; disable or unlink the custom app
   - Grok/Gemini: disable connectors in the provider UI; stop named/quick tunnels
   - Local agents: stop the local client; do not leave public tunnels running
4. **Stop facade ingress**
   Terminate the process started with `DCP_FACADE_TRANSPORT=streamable-http`.
   Confirm no listener remains on `127.0.0.1:<FACADE_PORT>`.
5. **Stop or leave backend sidecars as needed**
   Optional: `uv run --frozen dopemux mcp stop --repo "<TARGET_WORKTREE>"`
   Stopping backends is **not** required for exposure rollback; adapters must
   already be unreachable once the facade is down and credentials revoked.

## Registry rollback

- Set registry-v2 targets `enabled: false` in the external registry file
  (`DCP_FACADE_REGISTRY_V2`), or remove the file path from the environment.
- Do not delete operator audit artifacts needed for forensics.

## Code rollback (series packets)

If a code regression is suspected:

```bash
# On a dedicated worktree only; do not force-push main without process
git revert <merge_commit_of_suspect_packet>
```

Packet-specific notes:

| Packet | Rollback effect |
| --- | --- |
| 0012 | Restores pre-v2 public tool surface if reverted |
| 0013 | Removes connector policy/auth primitives |
| 0014 | Removes loopback ingress; keep `DCP_FACADE_TRANSPORT=stdio` |
| 0015 | Removes ownership/safe-adapter gates |
| 0016 | Docs/templates only |

## Verification after disable

```bash
# Expect connection refused or auth failure
curl -sS -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:<FACADE_PORT>/mcp" || true
# Provider UI: tool discovery fails or connector disabled
```

Confirm:

- No public tool discovery from providers
- No raw secrets in remaining logs
- Backend services (if still running) are not exposed without the facade

## Do not

- Leave quick tunnels running “for later”
- Reuse one connector credential across providers
- Commit disabled-but-populated secrets “for convenience”
- Point providers at ConPort/dope-memory ports directly
