---
id: dcp-mcp-readonly-provider-command-ledger
title: DCP Provider Command Verification Ledger
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
last_review: '2026-07-16'
next_review: '2026-10-14'
prelude: Commands documented for DCP multi-provider setup verified against local --help or source in TP-0016.
---

# Provider Command Verification Ledger

Packet: **TP-DCP-MCP-RO-0016**
Worktree verification date: **2026-07-16**
Repo head at verification: bound to the TP-0016 PR head after implementation.

| Command / surface | Verified how | Status |
| --- | --- | --- |
| `dopemux mcp --help` | `uv run --frozen dopemux mcp --help` | PASS |
| `dopemux mcp start --help` | local `--help` (options: `--repo`, `--services`, `--dry-run`, `--json`) | PASS |
| `dopemux mcp doctor --help` | local `--help` (`--repo`, `--json`, `--verbose`, `--skip-docker`) | PASS |
| `dopemux mcp init` / `repair-config` / `status` / `stop` | listed under `dopemux mcp --help` | PASS (existence) |
| `DCP_FACADE_TRANSPORT` | `services/dcp-readonly-facade/src/mcp/server.py` | PASS |
| `DCP_FACADE_INGRESS_HOST` / `PORT` / `CONNECTOR_POLICY` | `loopback_server.py` | PASS |
| `DCP_FACADE_REGISTRY_V2` | `server.py` / `registry_v2.py` | PASS |
| `curl` health `/health` and `/mcp` | TP-0014 contract + tests | PASS (contract) |
| `tunnel-client …` | not installed locally; documented as OBSERVED vendor shape | NOT_RUN (vendor) |
| `cloudflared tunnel --url` / `ngrok http` | not executed live; documented as OBSERVED vendor smoke shape | NOT_RUN (vendor) |

Rules:

- Vendor CLI flags that were **not** re-verified same-day are labeled NOT_RUN.
- Operators must re-check official provider docs before live use (see
  [`SOURCE_DATE_LEDGER.md`](SOURCE_DATE_LEDGER.md)).
