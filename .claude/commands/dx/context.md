---
description: "Show full task-orchestrator context — gate status, missing notes, guidance pointer, schema"
arguments: "[<item-id-or-prefix>] [--since <iso8601>]"
allowed-tools: [
  "Read", "Bash",
  "mcp__task-orchestrator__get_context",
  "mcp__task-orchestrator__query_notes",
  "mcp__conport__get_active_context"
]
model: "claude-sonnet-4-5"
---

# /dx:context — Orchestrator Context Snapshot

Three modes, picked automatically based on arguments:

| Arguments | Mode | Behavior |
|---|---|---|
| `<item-id-or-prefix>` | **Item mode** | Show full gate status + schema + notes for one item |
| `--since <timestamp>` | **Session resume** | Show items with recent role transitions since timestamp |
| (none) | **Health check** | Active items (work/review) + blocked items + stalled items across the workspace |

---

## Phase 1: Mode Detection

Parse `$ARGUMENTS`:

- If first arg looks like a UUID or hex prefix (≥4 hex chars) → **Item mode**
- Else if `--since <timestamp>` provided → **Session resume mode**
- Else → **Health check mode**

---

## Phase 2a: Item Mode

Call `mcp__task-orchestrator__get_context(itemId="<id>")`.

Render:

```
┌─ <title> ───────────────────────────────────────────
│  ID:           <full-uuid>
│  Role:         <queue | work | review | terminal | blocked>
│  Status label: <statusLabel or "—">
│  Priority:     <priority>  │  Complexity: <complexity or "—">
│  Tags:         <comma-list>
│  Depth:        <depth>
└─────────────────────────────────────────────────────

Gate status (current phase: <phase>):
  canAdvance: <true | false>
  Missing required notes: <comma-list of keys, or "—">

Note progress: <filled>/<total> required notes filled
  (remaining: <remaining>)

Guidance pointer:
  <guidancePointer text, or "(no schema or all required filled)">

Schema-expected notes:
  <for each entry in `schema`:>
    [✓ filled | ✗ missing] <key> (<role>, <required ? "required" : "optional">)
       <description>
       <if guidance: "  → "guidance text">
       <if skill: "  → skill: <skill-name>">
```

If the item has live notes, also show:

```
Filed notes (filed > 0):
  - <key> (<role>) — <first 80 chars of body>...
```

---

## Phase 2b: Session Resume Mode

Call `mcp__task-orchestrator__get_context(since="<timestamp>")`.

Render:

```
═══ Session resume since <timestamp> ═══

Active items (currently in work or review):
<for each item:>
  ▸ <title>
      ID: <short-prefix>  │  Role: <role>  │  Tags: <tags>
      Ancestors: <breadcrumb>

Recent role transitions:
<for each transition (most recent first):>
  • <timestamp> — <item title>: <from-role> → <to-role> (<trigger>)
      Actor: <actor.id or "—">  │  Summary: <summary or "—">

Stalled items (active but missing required notes):
<for each stalled item:>
  ⚠️ <title>
      Missing: <comma-list of missing required note keys>
      Guidance: <guidancePointer>
```

This is the standard "where was I?" view after a context-switch break.

---

## Phase 2c: Health Check Mode

Call `mcp__task-orchestrator__get_context()` (no parameters).

Render:

```
═══ Workspace orchestrator health ═══

Active items (<N>):
<for each item in activeItems:>
  ▸ [<role>] <title>  (<short-prefix>)

Blocked items (<N>):
<for each item in blockedItems:>
  ⛔ <title>  (<short-prefix>)
      <if blockers info available:>
        Waiting on: <comma-list of blocker titles>

Stalled items (<N>):
<for each item in stalledItems:>
  ⚠️ <title>  (<short-prefix>)
      Missing required notes for <phase>

If all three lists are empty:
  ✅ All clear. Workspace has no active, blocked, or stalled items.
  Try /dx:next to start something.
```

---

## Phase 3: Notes Detail (Item Mode Only)

If item mode AND the user wants full note bodies, optionally call `mcp__task-orchestrator__query_notes(operation="list", itemId="<id>", includeBody=true)` and print:

```
─── All notes on this item ───
<for each note:>
  ## <key> (<role>) — note id <short-prefix>
  <body>
```

Default: only show note headers in Item mode. User can ask explicitly for bodies.

---

## Phase 4: ConPort Cross-Check (Optional, Item Mode)

If `mcp__conport__get_active_context` is available, fetch it and compare:

- If `current_focus` mentions this item ID or title → annotate as "(this is your current focus per ConPort)"
- If `last_task_status` differs from the orchestrator's role → flag potential drift

---

## Error Handling

**Item not found**:
```
❌ No item found for ID/prefix "<input>".
  Try:
  - mcp__task-orchestrator__query_items operation=search query="<keywords>"
  - /dx:next  to see active candidates
  - /dx:tree  to see the full hierarchy
```

**Orchestrator MCP unavailable**: same fallback message as /dx:next.

**Schema-less mode** (`guidancePointer: null`, `schema: []`):
```
ℹ️  No schema loaded. canAdvance always true; no gate enforcement.
  This is expected pre-config or when items have no matching schema tag.
  Once .taskorchestrator/config.yaml ships and MCP restarts, guidance will surface.
```

---

## Success Criteria

- ✅ Mode picked correctly from arguments
- ✅ All relevant fields displayed (no silent omissions)
- ✅ Gate status is clear: canAdvance + missing notes + guidance pointer
- ✅ Schema details visible when loaded; clear "no schema" message when not
- ✅ Session resume surfaces actor + transition history
- ✅ Health check returns clear next-action ("nothing active" vs "X blocked items")

---

## Notes for Claude

- Item mode is the most common use; default rendering should be Item mode-friendly.
- Don't dump all notes by default — show headers, let user ask for bodies.
- Breadcrumb ancestors render root → leaf with " > " separators.
- Color/emoji: ▸ for active, ⛔ for blocked, ⚠️ for stalled, ✅ for clear.
- Times in session resume should be human-readable ("3h ago") with full ISO in parentheses.
