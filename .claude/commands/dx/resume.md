---
description: "Resume a blocked work-item (resume trigger) back to its saved previous role"
arguments: "<id-or-prefix>"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_context",
  "mcp__task-orchestrator__advance_item"
]
model: "claude-sonnet-4-5"
---

# /dx:resume — Unblock a Work-Item (resume trigger)

Restore a `blocked` item to the role it held before it was blocked. The inverse of `/dx:block`.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

- First positional → `<id-or-prefix>`. **Required.**

---

## Phase 2: Safety & Confirmation (MUTATES state)

**2a — Preflight.** `get_context(itemId="<id>")`. Read `role`.

**2b — Guard.**
- `role != "blocked"` → stop: "Item isn't blocked (role: `<role>`); nothing to resume. `/dx:start <id>` to advance a queue/work item."

**2c — Transition.**
```
advance_item({ itemId: "<id>", trigger: "resume", summary: "resumed via /dx:resume" })
```
Restores the saved `previousRole` (BLOCKED → previousRole).

---

## Phase 3: Render Result

```
▸ Resumed: <title>   (blocked → <newRole>)
   Back in: <newRole>
```

Inspect `results[0].newRole` from the transition response. If it is `blocked` (the item has an unsatisfied dependency, not just an explicit hold), `resume` cleared the explicit hold but the BLOCKS edge remains — surface:
```
⚠️ Still blocked by an unsatisfied dependency. /dx:resume cleared the explicit hold but a BLOCKS edge remains. See /dx:blocked <id>.
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:context <id>   → confirm the restored role + gate status
  /dx:note <id> <key>→ fill notes for the current phase
  /dx:complete <id>  → when required notes are filled
```

---

## Error Handling

**Item not found** / **not blocked** (handled in 2b) / **orchestrator unavailable**: report clearly; fall back to `advance_item({itemId, trigger:"resume"})` directly.

---

## Success Criteria

- ✅ Refuses to act on non-blocked items with a clear redirect.
- ✅ Restores the exact saved `previousRole`.
- ✅ Surfaces dependency-driven re-block when it happens.

---

## Notes for Claude

- **Mutates state.** `resume` is only valid from `blocked`; the orchestrator returns the item to its saved `previousRole`, not to a fixed role.
- For dependency-blocked items, the real fix is satisfying the blocker (advance the blocking item), not `/dx:resume` — resume only clears explicit blocks.
