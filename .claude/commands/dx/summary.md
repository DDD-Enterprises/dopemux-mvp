---
description: PM-ready project dashboard — all work-items by container with status, gates, and ranked next actions (read-only)
arguments: "[optional: container UUID or title to scope the dashboard]"
allowed-tools: mcp__task-orchestrator__query_items, mcp__task-orchestrator__get_context, mcp__task-orchestrator__get_next_item
model: claude-sonnet-4-5
---

# /dx:summary — Project Dashboard

**Authority**: task-orchestrator MCP per AGENTS.md §6 + adr-task-orchestrator-as-workflow-authority. Read-only wrapper — issues NO writes. Adapted from upstream `work-summary` skill (TP-CS-101 / Path B).

## Phase 1 — Parse arguments

`$ARGUMENTS` may be empty, a container UUID, or a title fragment.
- Empty → global (unscoped) dashboard.
- Looks like a UUID → use directly as `parentId`.
- Text → `query_items(operation="search", query="<text>")`, pick the best-matching root/container, use its UUID as `parentId`. If ambiguous, ask which one.

## Phase 2 — Fetch (3 calls, in parallel)

1. `query_items(operation="overview", includeChildren=true)` — root items with per-role child counts + direct children (id, title, role, statusLabel, priority, tags, type, childCounts). Add `itemId="<parentId>"` when scoped.
2. `get_context()` — health-check: active (work/review), blocked, stalled item sets.
3. `get_next_item(limit=5)` — dependency-aware ranked recommendations. Add `parentId` when scoped.

## Phase 3 — Render (ADHD-scannable)

Group by container. For each item show: short id (first 8 chars), title (truncate ~55), role, priority, tags. Cross-reference the get_context sets to mark state with the legend:
`▸ active · ⛔ blocked · ⚠️ stalled · ✅ clear`
Cap each container's item list at ~10 (note "… N more"). Lead with a one-line health summary (totals: N active, N blocked, N stalled). Add brief observations ONLY for genuine anomalies (e.g., a container with everything blocked).

## Phase 4 — Footer

`Next actions:` (≤3):
- `/dx:next` — pick the top-ranked item to work
- `/dx:context <id>` — gate status + missing notes for a specific item
- `/dx:blocked` — blocker chains if anything is stuck

## Error handling
- No items → friendly empty-state ("No work-items yet — create one with the orchestrator MCP").
- Scoped search with no match → say so, fall back to global or ask.

## Success criteria
Operator sees the full project state in one scannable view in <10s, with enough detail (ids, tags, state) to decide what to do next. No writes performed.

## Notes for Claude
This is the aggregate dashboard; `/dx:tree` (structure), `/dx:next` (one pick), and `/dx:context` (one item's gates) are the narrower views. Prefer this when the user asks "what's the state / where did I leave off / project health".
