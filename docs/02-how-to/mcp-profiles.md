---
id: mcp-profiles
title: "MCP Profiles \u2014 Task-Selected Tool Plane"
type: how-to
owner: '@hu3mann'
date: '2026-07-26'
status: active
author: '@hu3mann'
last_review: '2026-08-23'
next_review: '2026-11-21'
prelude: "MCP Profiles \u2014 Task-Selected Tool Plane (how-to) for dopemux documentation\
  \ and developer workflows."
---
# MCP Profiles (ADR-DMX-MCPPROF-001)

Profiles are **exposure projections** declared in `mcp_catalog.yaml`. They do
not change the authority of ConPort, dope-memory, task-orchestrator, dope-context,
or any other plane.

There is **no implicit `all` profile**. Unknown profiles fail closed.

## Compatibility default

When a command needs a profile and none is supplied, Dopemux resolves the
explicitly named compatibility profile:

```text
core-code
```

Never every catalog server.

## Initial profiles

| Profile | Use | Servers (summary) |
|---|---|---|
| `core-code` | Normal implementation | GitHub RO, ConPort, dope-memory, task-orchestrator, Serena |
| `core-retrieval` | Broad retrieval | GitHub RO, ConPort, dope-memory, task-orchestrator, dope-context |
| `planning-audit` | Plan / challenge / audit | GitHub RO, dope-context, **pal-stdio** (not PAL HTTP) |
| `ui-audit` | Stateful UI investigation | GitHub RO, Playwright MCP, repo-domain-read (when contract ok) |
| `research-docs` | Vendor docs | GitHub RO, Context7 |
| `research-web` | Deep research | GitHub RO, GPT Researcher |
| `security` | Security review | GitHub security toolsets, Semgrep |
| `pr-steward` | PR evidence | GitHub PR/Actions reads, dcp-readonly-facade |

`core-code` and `core-retrieval` are alternatives, not cumulative defaults.

## CLI

```bash
# List declared profiles
dopemux mcp profile list

# Show inventory + digests
dopemux mcp profile show core-code
dopemux mcp profile show core-code --json

# Profile doctor overlay (no Docker)
dopemux mcp doctor --profile core-code
dopemux mcp doctor --profile ui-audit --json

# Init / generate with an explicit profile
dopemux mcp init --profile core-code
dopemux mcp generate --profile core-code --output-dir /tmp/mcp-out --apply

# Agent-matrix fleet projection (ADR-MCPINT-001 parity) — not profile=all
dopemux mcp generate --agent-matrix
```

Forbidden profile names: `all`, `*`, `any`, `full`, `everything`.

## Invariants

1. **PAL HTTP** (`pal`) is health-only. Profiles use **`pal-stdio`** for PAL MCP.
2. **Playwright MCP** is only for `ui-audit`. Routine coding/CI uses Playwright CLI.
3. **Desktop Commander** is not in any normal profile.
4. **GitHub** is read-only on normal profiles (`GITHUB_READ_ONLY=1` / `--read-only`).
5. **ConPort admin tools** (`fork_instance`, `promote`, `promote_all`) are excluded unless a profile sets `admin: true` (none do today).
6. **Tool inventory drift** fails closed when visible tool count exceeds the checked-in `inventory_baseline`.
7. **repo-domain-read** only when:
   - executable: `<repo-root>/scripts/mcp/domain-read` (tracked regular file, no symlink escape)
   - manifest: `<repo-root>/mcp/domain-read-tools.json`
   - every tool `side_effect: READ_ONLY_NO_DURABLE_SIDE_EFFECT`

## Digests

Each resolved profile emits:

- `profile_digest` — SHA-256 of canonical selected servers + visible tools + GitHub policy
- `tool_schema_digest` — SHA-256 of visible tool schema payload from `mcp_tool_surfaces.json`

Use these in proof and CI. Unexplained tool-count increases require a baseline update with rationale.

## Migration

1. Prefer `dopemux mcp profile show <name>` before changing agent configs.
2. Scaffold worktrees with `dopemux mcp init --profile core-code` (or omit `--profile` for the same compatibility default when profiles are declared).
3. Do not hand-edit generated agent configs to add servers — edit `mcp_catalog.yaml` profiles and regenerate.
4. Agent-matrix generate (`--agent-matrix`) remains for OpenCode/Codex/Copilot parity; it is **not** an “all tools” task profile.

## Related

- ADR: [`docs/90-adr/adr-mcpprof-001-profiled-tool-plane-and-domain-facades.md`](../90-adr/adr-mcpprof-001-profiled-tool-plane-and-domain-facades.md)
- Catalog authority: `mcp_catalog.yaml`
- System reference: [`.claude/mcp-system.md`](../../.claude/mcp-system.md)
- Transport rules: `AGENTS.md` §12
