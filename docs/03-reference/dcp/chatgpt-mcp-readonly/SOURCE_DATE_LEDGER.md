---
id: dcp-mcp-readonly-source-date-ledger
title: DCP Multi-Provider Source Date Ledger
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Source-date tracking for provider documentation used by the DCP multi-provider series.
---

# Source Date Ledger

Packet: **TP-DCP-MCP-RO-0016**

| Source | Class | Date captured | Notes |
| --- | --- | --- | --- |
| Supervisor package `PROVIDER-SETUP-GUIDE.md` | advisory package | 2026-07-16 (package ZIP) | SHA-256 `c0cb9d34…2447`; placeholders only |
| Supervisor package `CONNECTOR-POLICY-EXAMPLE.yaml` | advisory package | 2026-07-16 | Already mirrored as repo example |
| Repo `CONNECTOR_POLICY_CONTRACT.md` | runtime-aligned docs | 2026-07-16 | TP-0013 |
| Repo `INGRESS_LOOPBACK_CONTRACT.md` | runtime-aligned docs | 2026-07-16 | TP-0014 |
| Repo `OWNERSHIP_AND_SAFE_ADAPTERS.md` | runtime-aligned docs | 2026-07-16 | TP-0015 |
| `dopemux mcp start --help` | local CLI | 2026-07-16 | Verified in TP-0016 worktree |
| OpenAI Secure MCP Tunnel / `tunnel-client` | vendor external | operator must refresh | Do not trust stale flags |
| xAI / Grok custom connectors | vendor external | operator must refresh | Public HTTPS + auth |
| Google Gemini remote MCP | vendor external | operator must refresh | Model/agent support may drift |
| Cloudflare / ngrok tunnel docs | vendor external | operator must refresh | Named vs quick tunnel tradeoffs |

## Refresh rule

Before any live provider enablement (TP-0017):

1. Re-run local CLI `--help` for Dopemux commands used in the runbook.
2. Re-check official provider docs the same day; record new dates here.
3. Fail closed if a documented vendor flag is missing or renamed.
