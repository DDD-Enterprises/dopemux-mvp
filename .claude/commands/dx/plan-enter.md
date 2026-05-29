---
description: Plan-mode entry — establish task-orchestrator context before exploring or planning (read-only)
arguments: "[optional: work-item UUID or title this plan relates to]"
allowed-tools: mcp__task-orchestrator__get_context, mcp__task-orchestrator__query_items, mcp__task-orchestrator__get_next_item
model: claude-sonnet-4-5
---

# /dx:plan-enter — Plan-Mode Entry Workflow

**Authority**: task-orchestrator MCP per AGENTS.md §6 + adr-task-orchestrator-as-workflow-authority. Read-only wrapper — issues NO writes. Adapted from upstream `pre-plan-workflow` skill (TP-CS-101 / Path B). The `PreToolUse[EnterPlanMode]` hook points here.

## Phase 1 — Parse arguments
`$ARGUMENTS` may name a related work-item (UUID or title). If a title, resolve via `query_items(operation="search", query="<text>")`.

## Phase 2 — Establish context (read-only)
1. `get_context()` — health-check: what's already active, blocked, stalled. A plan should not duplicate an in-flight item.
2. If a related item was named: `get_context(itemId="<uuid>")` — its role, gate status, missing notes, guidancePointer.
3. `get_next_item(limit=3)` — what the orchestrator would pick next, so the plan aligns with ranked priorities.

## Phase 3 — Render (orientation brief)
Summarize, scannably:
- Active/blocked/stalled counts (don't start a plan that collides with active work).
- If a related item exists: its current role + what the next phase expects (so the plan targets the right phase).
- Whether this plan should become a NEW work-item or attach to an existing one.

## Phase 4 — Footer
`Next actions:` (≤3):
- Proceed to explore + draft the plan, scoped to the gap identified above
- `/dx:context <id>` — deeper gate detail on the related item
- On plan approval, run `/dx:plan-exit` to materialize work-items

## Error handling
- Orchestrator unreachable → say so; planning may proceed but materialization (`/dx:plan-exit`) will be needed once it's back.

## Success criteria
Before any exploration/plan writing, the operator knows what's already in flight and which work-item (new or existing) this plan maps to. No writes performed.

## Notes for Claude
This is orientation only — it does NOT create work-items. Creation/dispatch happens at `/dx:plan-exit` after the plan is approved. Keep it fast; it runs at plan-mode entry.
