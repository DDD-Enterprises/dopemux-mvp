---
id: pal-mcp-codex-claude-stdio
title: Pal Mcp Codex Claude Stdio
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-27'
last_review: '2026-06-27'
next_review: '2026-09-25'
prelude: Pal Mcp Codex Claude Stdio (explanation) for dopemux documentation and developer
  workflows.
---
# PAL MCP — Codex & Claude Code (operator runbook)

Dopemux also ships `mcp-pal` / `mcp-pal-stdio` in `compose.yml` (HTTP :3003 and toolkit
stdio). **This runbook covers the standalone checkout** used by Codex today:

`~/code/pal-mcp-server` → container `pal-mcp-server`

Canonical detail lives in the PAL repo:
[docs/CODEX-CLAUDE-STDIO-SETUP.md](https://github.com/hu3mann/pal-mcp-server/blob/main/docs/CODEX-CLAUDE-STDIO-SETUP.md)

## One-time setup

```bash
cd ~/code/pal-mcp-server
git remote add fork https://github.com/hu3mann/pal-mcp-server.git 2>/dev/null || true
git pull fork main
cp .env.example .env   # add ≥1 API key; no inline comments on key lines
docker compose up -d --build
```

## Client config (local, not in git)

| Client | File | Transport |
|--------|------|-----------|
| Codex | `~/.codex/config.toml` | `[mcp_servers.pal]` → `docker exec -i pal-mcp-server /opt/venv/bin/python server.py` |
| Claude Code | `~/.claude.json` → `mcpServers.pal` | same stdio `docker exec` block |

Copy-paste snippets: `pal-mcp-server/examples/codex-pal-mcp.toml` and `examples/claude-pal-mcp.json`.

**Do not** use `"type": "sse"` / `localhost:3003` — PAL is stdio-only in this layout.

## Verify

```bash
docker ps --filter name=pal-mcp-server   # Up (healthy)
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n' \
  | docker exec -i pal-mcp-server /opt/venv/bin/python server.py | head -1
# expect serverInfo.name == PAL
```

Restart Codex / Claude Code after config edits.

## Troubleshooting (2026-06-15 incident)

| Symptom | Fix |
|---------|-----|
| Handshake / connection refused | Container down or wrong name → `docker compose up -d` |
| Empty API keys in container | Recreate after filling `.env`: `docker compose up -d --force-recreate` |
| Wrong python path | Use `/opt/venv/bin/python` not `/app/.venv/bin/python` |
| Network pool overlap | Use current `docker-compose.yml` (no fixed 172.20.0.0/16 subnet) |

## Fork / upstream

- Operator fork (merged): [hu3mann/pal-mcp-server](https://github.com/hu3mann/pal-mcp-server)
- Upstream PR: [BeehiveInnovations/pal-mcp-server#452](https://github.com/BeehiveInnovations/pal-mcp-server/pull/452)
