---
description: Plan-mode exit — materialize approved plan into task-orchestrator work-items and dispatch implementation
arguments: "[optional: parent work-item UUID to attach the materialized items under]"
allowed-tools: mcp__task-orchestrator__get_context, mcp__task-orchestrator__query_items, mcp__task-orchestrator__create_work_tree, mcp__task-orchestrator__manage_items, mcp__task-orchestrator__advance_item
model: claude-sonnet-4-5
---

# /dx:plan-exit — Plan-Mode Exit Workflow

**Authority**: task-orchestrator MCP per AGENTS.md §6 + adr-task-orchestrator-as-workflow-authority. WRITE command — creates work-items. Adapted from upstream `post-plan-workflow` skill (TP-CS-101 / Path B). The `PostToolUse[ExitPlanMode]` hook points here.

## Phase 1 — Parse arguments
`$ARGUMENTS` may name a parent work-item (UUID) to attach materialized items under. If a title, resolve via `query_items(operation="search", ...)`.

## Phase 2 — Materialize (with confirmation)

### Safety & confirmation (MANDATORY before any write)
1. Read the approved plan from the current conversation (the plan that was just approved on ExitPlanMode).
2. Derive the work-item breakdown: a parent task-packet + child items per discrete deliverable.
3. **Preflight read**: `get_context()` to confirm no duplicate in-flight item already covers this.
4. **Present the proposed tree** (titles, types, parent) and get explicit operator confirmation BEFORE creating. Never materialize blind.

### Create
- Use `create_work_tree` for an atomic parent+children hierarchy, OR `manage_items(operation="create", ...)` for a single item.
- Set `type="task-packet"` (or the right schema type) on change-producing items so the proof-bundle complete-gate activates.
- Carry the actor on writes: `{id:"worktree-<basename>-<branch>", kind:"subagent", parent:"<session-id>"}`.

### Dispatch
- Hand off to `/dx:implement <id>` for the first item, OR advance the chosen item with `advance_item(trigger="start", actor=...)` and brief the implementer.

## Phase 3 — Render
Show the created tree (short ids + titles + roles) and which item implementation starts on.

## Phase 4 — Footer
`Next actions:` (≤3):
- `/dx:implement <id>` — start the first materialized item
- `/dx:next` — confirm the orchestrator's ranked pick
- `/dx:tree <parent>` — view the materialized hierarchy

## Error handling
- Operator declines confirmation → create nothing; report the proposed tree for later.
- Orchestrator unreachable → do NOT partially create; report and retry when back.

## Success criteria
The approved plan exists as a gated work-item tree in the orchestrator, with implementation dispatched, and nothing was created without explicit confirmation.

## Notes for Claude
This is the only `/dx:` plan-mode command that writes. Always preflight + confirm. Do NOT edit `.taskorchestrator/config.yaml` (contract-sensitive, ADR-gated). If the plan maps to an existing item, attach/advance rather than duplicating.
