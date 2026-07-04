---
id: fleet-generated-outputs
title: Fleet Generated Outputs
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-03'
last_review: '2026-07-03'
next_review: '2026-10-01'
prelude: Fleet Generated Outputs (reference) for dopemux documentation and developer
  workflows.
---
# MCP Fleet Generated Outputs

`dopemux mcp generate` renders reviewable MCP fleet projections from
`mcp_catalog.yaml`.

Generated paths:

- `local/.mcp.json` mirrors the catalog default per-worktree MCP servers.
- `claude/mcpServers.json` contains the singleton Claude global fragment.
- `codex/config.toml` contains singleton stdio and streamable HTTP MCP servers
  in Codex TOML syntax.
- `health/mcp-health-probes.json` lists catalog health URLs and compose service
  bindings plus role, lifecycle, identity, management, and follow-on decision
  metadata for static probe planning.
- `docs/mcp-fleet.md` renders the catalog doctrine summary.

Dry-run is the default and writes nothing:

```bash
dopemux mcp generate
```

Writing generated files requires an explicit bounded directory:

```bash
dopemux mcp generate --apply --output-dir proof/mcp-generated-preview
```

The command does not write user-global files. Operators must review generated
fragments before copying or applying them to global config surfaces.

## Server Personality Metadata

The canonical catalog records each MCP server's plane, authority role,
lifecycle, management model, identity scope, and follow-on decision. These
fields are contract data, not runtime proof.

Static gates currently pin the high-risk fleet roles:

- ConPort remains structured context authority in the memory plane.
- task-orchestrator remains workflow authority with repo-scoped singleton state.
- dope-memory remains chronicle authority with per-worktree capture identity.
- dope-context remains read-only retrieval projection with per-call workspace
  identity.
- PAL remains reasoning infrastructure with explicit operator-managed stdio
  handling.
- Exa remains decision-gated for a future wire-or-retire scan.
- desktop-commander remains decision-gated for a future delete-or-host-run
  decision.
