---
description: "Show task-orchestrator work-item tree — root overview or scoped subtree with child counts by role"
arguments: "[<item-id-or-prefix>] [--limit N] [--offset N] [--include-children]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__query_items"
]
model: "claude-sonnet-4-5"
---

# /dx:tree — Work-Item Tree Overview

Render the orchestrator's work-item hierarchy. Two modes:

| Arguments | Mode | Behavior |
|---|---|---|
| `<item-id-or-prefix>` | **Scoped** | Show parent metadata + child counts by role + direct children list for one tree. |
| (none) | **Global** | Show all root items (depth=0) with per-root child counts. |

**Purpose**: orient operator quickly on the workspace shape — what trees exist, what's active under each, where work is queued vs blocked.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

---

## Phase 1: Argument Parsing

Parse `$ARGUMENTS`:

- First positional arg looks like a UUID or hex prefix (≥4 chars) → **Scoped mode** (`itemId`).
- `--limit N` → cap root items in global mode (default: 10 for ADHD-friendly disclosure). The orchestrator caps `limit` at 50 per call; use `--offset` to page beyond.
- `--offset N` → skip the first N root items (for paging through workspaces with many roots; default: 0).
- `--include-children` → include direct children array in global mode (default: false to keep output scannable).

If no positional arg and no flags → Global mode with `limit=10, offset=0, includeChildren=false`.

---

## Phase 2: Fetch

### Scoped mode

```
query_items(operation="overview", itemId="<id>")
```

Response includes: item metadata, `childCounts: { queue, work, review, blocked, terminal }`, and `children: [...]` array.

### Global mode

```
query_items(operation="overview", limit=<N>, offset=<M>, includeChildren=<flag>)
```

Response includes all root items (depth=0) each with `childCounts`.

---

## Phase 3: Render

### Scoped mode

```
┌─ <title> ───────────────────────────────────────────
│  ID:           <short-prefix> (full: <full-uuid>)
│  Role:         <queue | work | review | terminal | blocked>
│  Status label: <statusLabel or "—">
│  Priority:     <priority>  │  Tags: <tags>
└─────────────────────────────────────────────────────

Child counts:
  queue: <N>  │  work: <N>  │  review: <N>  │  blocked: <N>  │  terminal: <N>

Direct children (<count>):
  ▸ [<role>] <title>  (<short-prefix>)  priority=<priority>
  ▸ [<role>] <title>  (<short-prefix>)  priority=<priority>
  ...
```

Order children by role (queue → work → review → blocked → terminal) then by priority (high first).

### Global mode

```
═══ Workspace work-item roots (showing <offset+1>..<offset+returned> of <total>) ═══

▸ <title>  (<short-prefix>)
    Tags: <tags>  │  Priority: <priority>
    Counts: queue=<N> work=<N> review=<N> blocked=<N> terminal=<N>
    <if --include-children: list direct children indented>

▸ <next root>
    ...
```

If `total === 0` → `(workspace has no root work-items yet — try /dx:next or manage_items to create one)`.

If more roots exist beyond the current page:
```
… <total - (offset + returned)> more roots. Page via:
  /dx:tree --offset <offset + limit> [--limit N] [--include-children]
```

---

## Phase 4: ADHD-Friendly Footer

After the cards/list:

```
Next actions:
  /dx:context <id>        → see full gate status + missing notes
  /dx:blocked             → see what's waiting on dependencies
  /dx:next [--scope <id>] → pick the next item under this tree
```

---

## Error Handling

**Orchestrator MCP unavailable**:
```
⚠️ task-orchestrator MCP not responding.
  Check: ls /Users/hue/plugins/dopemux-mission-control/scripts/
  Or restart your Claude Code session.
  Fallback: query manually via mcp__task-orchestrator__query_items.
```

**Item not found (scoped mode)**:
```
❌ No item found for ID/prefix "<input>".
  Try:
  - mcp__task-orchestrator__query_items operation=search query="<keywords>"
  - /dx:search  to look up by text
  - /dx:tree    (no args) to list workspace roots
```

---

## Success Criteria

- ✅ Correct mode picked from arguments.
- ✅ Counts by role visible (no manual roll-up needed).
- ✅ Children sorted role → priority within scoped mode.
- ✅ Global view limited to 10 roots by default (ADHD-friendly).
- ✅ Output scannable in <10 seconds.

---

## Notes for Claude

- Default `limit=10` for global mode; orchestrator caps `limit` at 50 per call. For workspaces with >10 roots, use `--offset` to page or `--limit N` (up to 50) to widen one page.
- `--include-children` adds noise; suggest only when operator is hunting across multiple roots.
- Short UUID prefixes are what operators type; show full UUID parenthetically once per card.
- Role order in renders: queue → work → review → blocked → terminal.
- This is a read-only wrapper. Never call `manage_items` or `advance_item` from this command.
