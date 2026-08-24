# MCP System Reference for Claude Code

**Status**: Operational — see `AGENTS.md §12` for transport rules and debug sequence
**Last Updated**: 2026-07-26

---

## System Overview

This project uses a Docker-based MCP ecosystem with two tiers:

- **Singleton servers** — shared across all worktrees, declared in `~/.claude.json`
- **Per-worktree servers** — isolated instances per workspace, declared in `.mcp.json`

The canonical server registry is [`mcp_catalog.yaml`](../mcp_catalog.yaml).

**Profiles (ADR-DMX-MCPPROF-001):** task-selected tool planes live under
`mcp_catalog.yaml` `profiles:`. There is **no implicit `all` profile**. See
[`docs/02-how-to/mcp-profiles.md`](../docs/02-how-to/mcp-profiles.md).

```bash
dopemux mcp profile list
dopemux mcp profile show core-code
dopemux mcp doctor --profile core-code
dopemux mcp init --profile core-code
```

Compatibility default when a profile is required and none is given: **`core-code`**.

---

## Session Start Protocol

Every session **should** begin with:

```
mcp__conport__get_active_context --workspace_id "<repo-root>"
mcp__conport__get_recent_activity_summary --workspace_id "<repo-root>" --hours_ago 24
```

Then: log decisions, track progress, preserve context before interruptions.

---

## Available MCP Servers

### Per-Worktree (in `.mcp.json`)

| Server | Transport | Port var | Purpose |
|---|---|---|---|
| `conport` | `sse` | `CONPORT_MCP_PORT` | Decisions, progress, knowledge graph |
| `dope-memory` | `http` | `DOPE_MEMORY_PORT` | Temporal chronicle, working context |
| `task-orchestrator` | `http` | `TASK_ORCHESTRATOR_HTTP_PORT` (fixed `7890`) | Workflow orchestration |

### Singleton (in `~/.claude.json`)

| Server | Transport | Port | Purpose |
|---|---|---|---|
| `pal` | `http` | `3003` | **Health/lifecycle only** — no MCP endpoint (`/mcp` 404). Do not use as PAL tools. |
| `pal-stdio` | `stdio` | — | **Sole PAL MCP surface** (thinkdeep, planner, codereview, precommit, …) |
| `serena` | `http` | `3006` | Semantic code intelligence (LSP + Tree-sitter) |
| `dope-context` | `http` | `3010` | Code/docs semantic search |
| `gpt-researcher` | `stdio` | — | Deep multi-source research |

> [!IMPORTANT]
> **PAL transport truth:** `pal` HTTP is a health shim only. Profiles and agents
> must use **`pal-stdio`** for PAL MCP tools. Planning/audit profile
> (`planning-audit`) selects `pal-stdio`, never `pal`.

### Profile-only specialized servers

| Server | Profile(s) | Notes |
|---|---|---|
| `github-official` | core-*, research-*, security, pr-steward, ui-audit | Official GitHub MCP, **read-only** |
| `playwright-mcp` | `ui-audit` only | Not for routine coding CI (use CLI) |
| `semgrep` | `security` | Security scans |
| `repo-domain-read` | `ui-audit` when contract ok | Fixed path `scripts/mcp/domain-read` |
| `context7` | `research-docs` | Host external docs lookup |
| `dcp-readonly-facade` | `pr-steward` | Planned-active until facade deploy |

Desktop Commander is **not** in any normal profile.

---

## Transport Architecture — Do Not Change Without Verification

> [!IMPORTANT]
> `dope-memory` and `task-orchestrator` use `"type": "http"` (Streamable HTTP).
> They are **not** SSE.  A `406 Not Acceptable` on `GET /mcp` is **correct behaviour**
> — it means you used the wrong HTTP method.  Always `POST` with JSON-RPC body.

| `type` value | Protocol | Client call |
|---|---|---|
| `"http"` | Streamable HTTP | `POST /mcp` + JSON-RPC body |
| `"sse"` | Server-Sent Events | `GET /sse` + `Accept: text/event-stream` |

---

## Setup in a New Workspace

```bash
cd ~/code/target-repo        # must be a git repo
dopemux mcp init --profile core-code   # or omit --profile for same compatibility default
source .envrc.dopemux-mcp    # load port variables
dopemux mcp doctor           # verify env + reachability
dopemux mcp doctor --profile core-code  # profile inventory overlay
```

Full guide: [`docs/02-how-to/mcp-setup-other-repos.md`](../docs/02-how-to/mcp-setup-other-repos.md)
Profiles: [`docs/02-how-to/mcp-profiles.md`](../docs/02-how-to/mcp-profiles.md)

---

## Health Monitoring

```bash
# Quick status:
dopemux mcp status

# Port + transport-aware probe:
./mcp_server_health_report.sh

# Per-server doctor:
dopemux mcp doctor

# Singleton sync (global ~/.claude.json):
dopemux mcp sync-globals
```

---

## Quick Command Reference

### ConPort

```bash
mcp__conport__get_active_context --workspace_id "<repo-root>"
mcp__conport__update_active_context --workspace_id "<repo-root>" --patch_content '{}'
mcp__conport__log_decision --workspace_id "<repo-root>" --summary "" --rationale ""
mcp__conport__log_progress --workspace_id "<repo-root>" --status "" --description ""
mcp__conport__log_system_pattern --workspace_id "<repo-root>" --name "" --description ""
```

### Recovery Commands

```bash
# Restart all MCP containers
cd ~/code/dopemux-mvp && dopemux mcp up

# Single service restart
docker compose -f compose.yml restart dope-memory

# Tail logs during a connection attempt
docker logs -f dopemux-dope-memory-1 2>&1 | grep -i "mcp\|error"
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `406 Not Acceptable` | Sent `GET` to Streamable HTTP endpoint | Change to `POST /mcp` with JSON-RPC |
| Connection refused | Container not running | `dopemux mcp up` |
| Port collision on `init` | Hash offset hit a singleton port | New version of `_allocate_ports` raises error with guidance |
| `task-orchestrator` on wrong port | Old `init` applied hash offset to wrapper-singleton | Re-run `dopemux mcp init --force` |
| Tools unavailable in session | Env vars not set at session start | `source .envrc.dopemux-mcp` before launching client |

Full reference: [`docs/02-how-to/mcp-transport-and-port-bugs.md`](../docs/02-how-to/mcp-transport-and-port-bugs.md)