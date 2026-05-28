---
description: "Preview a work-item's next legal transition (get_next_status) — read-only"
arguments: "<id-or-prefix>"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_next_status"
]
model: "claude-sonnet-4-5"
---

# /dx:preview — Preview the Next Transition (read-only)

Answer "what's the next legal move for this item, and is it ready?" without mutating anything. The non-destructive companion to `/dx:start` and `/dx:complete`.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

- First positional → `<id-or-prefix>`. **Required.**

> **Contract note:** `get_next_status` takes **only `itemId`** and *returns* the recommended next transition. It does **not** accept a `trigger` to preview an arbitrary transition (the plan's `/dx:preview <id> <trigger>` shape is not supported by the tool). This command shows the orchestrator's recommended next move.

---

## Phase 2: Fetch

```
get_next_status(itemId="<id>")
```
Returns `recommendation` (`Ready` | `Blocked` | `Terminal`) plus:
- Ready → `currentRole`, `nextRole`, `trigger` (e.g. `"start"`), `progressionPosition`
- Blocked → `currentRole`, `blockers[]` (each `fromItemId`, `currentRole`, `requiredRole`), or a resume suggestion if the item is in BLOCKED role
- Terminal → `currentRole`, `reason`

---

## Phase 3: Render

```
🔮 Next move for <title>  (<short-prefix>)

<if Ready:>
  ✅ Ready: <currentRole> → <nextRole>   (trigger: <trigger>)
     Run the command matching <trigger>:
       start → /dx:start · complete → /dx:complete · resume → /dx:resume   (<short-prefix>)

<if Blocked:>
  ⛔ Blocked (current role: <currentRole>)
     <if BLOCKED role: "Explicitly held — /dx:resume <id>">
     <else: blockers list:>
       • <blocker title> (<short-prefix>) — needs to reach <requiredRole>, currently <currentRole>

<if Terminal:>
  🏁 Terminal — <reason>. Nothing to advance. (/dx:reopen <id> to revive.)
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:start <id>     → apply the transition (when Ready)
  /dx:context <id>   → full gate status + notes
  /dx:blocked        → see the whole blocked picture (when Blocked)
```

---

## Error Handling

**Item not found** / **orchestrator unavailable**: report clearly; fall back to `get_next_status(itemId=...)` directly.

---

## Success Criteria

- ✅ Shows the recommended next transition without mutating state.
- ✅ Ready/Blocked/Terminal each render with the actionable next step.
- ✅ Blockers list their required vs current role.

---

## Notes for Claude

- **This is a read-only wrapper. Never mutate workflow state from this command.**
- `get_next_status` is `itemId`-only; it recommends a single next trigger (it does not simulate an arbitrary one). For the gate detail behind a transition, use `/dx:context <id>`.
