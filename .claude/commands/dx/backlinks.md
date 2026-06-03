---
description: "Show what blocks a work-item (query_dependencies incoming) — read-only"
arguments: "<id-or-prefix> [--type BLOCKS|IS_BLOCKED_BY|RELATES_TO]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__query_dependencies"
]
model: "claude-sonnet-4-5"
---

# /dx:backlinks — What Blocks This Item? (read-only)

Show the dependency edges pointing **at** an item — i.e. what must progress before this item can. The read companion to `/dx:depends`.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

- First positional → `<id-or-prefix>`. **Required.**
- `--type <BLOCKS|IS_BLOCKED_BY|RELATES_TO>` → optional edge-type filter (default: all types).

---

## Phase 2: Fetch

```
query_dependencies({
  itemId: "<id>",
  direction: "incoming",      // edges where this item is the toItemId — things that block it
  type: <if --type provided>,
  includeItemInfo: true
})
```

**Direction reminder:** `incoming` = edges pointing AT `<id>` = the prerequisites. (Use `/dx:depends` to create, `direction:"outgoing"` to ask "what does this item block?".)

---

## Phase 3: Render

```
🔗 What blocks <title>  (<short-prefix>)

<for each incoming edge:>
  ⛔ <fromTitle>  (<short-prefix>)   [<type>]
       role: <currentRole>   │   unblockAt: <edge unblockAt if present, else "—">
       → this item stays blocked until the prerequisite reaches that role

<if none:>
  ✅ Nothing blocks this item (no incoming dependencies<, of type <type>> if filtered).
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:depends <from> <id>  → add another prerequisite
  /dx:blocked              → workspace-wide blocked view with unblock thresholds
  /dx:context <from-id>    → inspect a blocker's gate status
```

---

## Error Handling

**Item not found** / **orchestrator unavailable**: report clearly; fall back to `query_dependencies(itemId=..., direction="incoming")` directly.

---

## Success Criteria

- ✅ Lists prerequisites (incoming edges) with type + blocker role.
- ✅ Empty result reads as a clear "nothing blocks this".
- ✅ `--type` filter narrows correctly.

---

## Notes for Claude

- **This is a read-only wrapper. Never mutate workflow state from this command.**
- `incoming` answers "what blocks X?"; for "what does X block?" query `direction:"outgoing"`. For a deep chain, `query_dependencies(neighborsOnly=false)` does a BFS traversal.
- This command surfaces each edge's stored `unblockAt` (when the dependency data includes it); `/dx:blocked` additionally computes `effectiveUnblockRole` and the satisfied/unsatisfied state across the workspace.
