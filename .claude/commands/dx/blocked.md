---
description: "List blocked work-items with blocker chains and unblock thresholds"
arguments: "[--scope <ancestor-uuid>] [--no-details]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_blocked_items"
]
model: "claude-sonnet-4-5"
---

# /dx:blocked — Blocked Work-Items

Surface items currently blocked — either explicitly in BLOCKED role, or with unsatisfied blocking dependencies.

**Purpose**: answer "what's stuck?" in one call. Each entry shows the block type, the blockers, and the threshold each blocker must reach to unblock.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

---

## Phase 1: Argument Parsing

Parse `$ARGUMENTS`:

- `--scope <ancestor-uuid>` → restrict to items under this parent (`parentId` param).
- `--no-details` → drop summary + tags from each blocked item (compact mode for very large block lists).

Defaults: workspace-wide; `includeBlockerDetails=true` (set false only when `--no-details` passed).

---

## Phase 2: Fetch

```
get_blocked_items({
  parentId: <if --scope provided>,
  includeBlockerDetails: <false if --no-details, else true>
})
```

Response shape:
```json
{
  "blockedItems": [
    {
      "itemId": "uuid",
      "title": "...",
      "role": "blocked" | "queue" | "work" | "review",
      "priority": "high" | "medium" | "low",
      "complexity": <int>,
      "blockType": "explicit" | "dependency",
      "blockedBy": [
        {
          "itemId": "uuid",
          "title": "...",
          "role": "...",
          "unblockAt": "queue" | "work" | "review" | "terminal",
          "effectiveUnblockRole": "...",
          "satisfied": true | false
        }
      ],
      "blockerCount": <int>,
      "ancestors": [{ "id": "...", "title": "...", "depth": <int> }]
    }
  ],
  "total": <int>
}
```

**Note**: Items in TERMINAL role are never included (per tool contract).

---

## Phase 3: Render

Group output by `blockType`. Within each group, sort by priority (high first) then by `blockerCount` (more blockers = higher up).

```
═══ Blocked items (<total> shown<, scoped to <ancestor>> if --scope) ═══

── Explicit blocks (blockType="explicit") ──
<for each item:>
  ⛔ <title>  (<short-prefix>)
      Role:       blocked  │  Priority: <priority>  │  Complexity: <complexity>
      Ancestors:  <breadcrumb>
      <if includeBlockerDetails (default): "Tags: <tags>" line; otherwise omit>
      <if blockedBy non-empty: blockedBy list — usually empty for explicit blocks>

── Dependency blocks (blockType="dependency") ──
<for each item:>
  ⛔ <title>  (<short-prefix>)
      Role:       <role>  │  Priority: <priority>
      Ancestors:  <breadcrumb>
      <if includeBlockerDetails (default): "Tags: <tags>" line; otherwise omit>
      Blockers (<blockerCount>):
        <for each blocker in blockedBy:>
          • [<role>] <blocker title>  (<short-prefix>)
              unblockAt: <unblockAt>  │  satisfied: <satisfied>
```

If `total === 0`:
```
✅ No blocked items in scope. Workspace is unblocked.
```

If only explicit blocks present, omit the dependency section header (and vice versa).

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:context <id>        → inspect a specific blocker's gate status
  /dx:resume <id>         → resume an explicitly-held item (when Phase 4 ships)
                            currently: advance_item(trigger="resume")
  /dx:next [--scope <id>] → pick something else under this tree
```

---

## Error Handling

**Orchestrator MCP unavailable**:
```
⚠️ task-orchestrator MCP not responding.
  Fallback: query manually via mcp__task-orchestrator__get_blocked_items.
```

**Invalid `--scope` UUID**:
```
❌ Could not resolve scope "<input>" to a work-item.
  Try /dx:tree to list valid roots, or pass a full UUID.
```

---

## Success Criteria

- ✅ Blocked items grouped by blockType for fast triage.
- ✅ Each item shows blocker chain with `unblockAt` thresholds.
- ✅ Empty scope returns a clear "all clear" message.
- ✅ Output scannable in <10 seconds (ADHD-friendly).

---

## Notes for Claude

- `blockType="explicit"`: item was paused via `advance_item(trigger="block")` or `hold`. Resume via `advance_item(trigger="resume")`.
- `blockType="dependency"`: item has an unsatisfied BLOCKS edge. It will auto-unblock when the blocker reaches its `unblockAt` role.
- `effectiveUnblockRole` may differ from `unblockAt` if the dependency was rewritten (rare); surface both when they diverge.
- This is a read-only wrapper. Never mutate workflow state from this command.
- For unblocking a stuck dependency manually, the operator should `/dx:context <blocker-id>` to fill any missing required notes.
