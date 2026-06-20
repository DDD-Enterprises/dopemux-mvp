---
description: "Chronicle recap from dope-memory (Memory Trinity plane 2)"
arguments: "[--hours N] [--workspace PATH]"
allowed-tools: [
  "Read", "Bash",
  "mcp__dope-memory__*"
]
model: "claude-sonnet-4-5"
---

# /mem:recap — Chronicle Recap (dope-memory)

Retrieve a temporal recap from **dope-memory** (chronicle plane). Read-only recap; canonical decisions remain in ConPort.

**Authority**: Memory Trinity plane 2 per `docs/90-adr/adr-dope-memory-as-chronicle-memory-authority.md`.

## Phase 1 — Preflight

1. Confirm `mcp__dope-memory__*` in per-worktree `.mcp.json`.
2. Source `.envrc.dopemux-mcp` if `dopemux mcp doctor` reports missing env.

## Phase 2 — Recap

1. Parse `--hours` (default 24) and optional `--workspace` (default repo root).
2. Call the dope-memory recap tool exposed by the active MCP surface (tool name per server manifest).
3. Render: timeline bullets, mirror receipt status if present, link to ConPort decision ids when mirrored.

## Phase 3 — Boundaries

- Recap is chronicle evidence, not canonical decision storage.
- On mirror `PARTIAL`, ConPort state is intact; report `mirror_status: FAILED` and do not rewrite ConPort.