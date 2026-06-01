---
description: "Explain why reopening terminal work-items is not currently exposed"
arguments: "<id-or-prefix>"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_context"
]
model: "claude-sonnet-4-5"
---

# /dx:reopen — Reopen Is Not Currently Exposed

Fail closed when asked to revive a terminal work-item. The deployed task-orchestrator MCP schema does not expose a `reopen` trigger on `advance_item`; do not emulate reopen with `cancel` or any other terminal transition.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

- First positional -> `<id-or-prefix>`. **Required.**

---

## Phase 2: Inspect Only

Call `get_context(itemId="<id>")` to identify the current role, status label, parent, and retained notes. This command is read-only even when the item is terminal.

If the item is not terminal, stop with the current role and point operators to the normal state commands:

- queue/work/review item that should pause -> `/dx:block <id>`
- blocked item that should resume -> `/dx:resume <id>`
- active item that should terminal -> `/dx:complete <id>` or `/dx:cancel <id>`

If the item is terminal, report that automatic reopen is unavailable in the current schema.

---

## Phase 3: Render Result

```
⛔ Reopen unavailable for <title>
   Current role: <role>
   statusLabel: <statusLabel or "—">

The deployed advance_item schema accepts only:
  start, complete, block, hold, resume, cancel

No state was changed.
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:context <id>  -> inspect retained notes and child state
  /dx:start <id>    -> only if the item is not terminal and can advance normally
  Create a new child/work item for follow-up work when terminal state must remain auditable
```

---

## Error Handling

**Item not found** / **orchestrator unavailable**: report clearly and do not mutate state.

---

## Success Criteria

- Refuses to invent or emulate a missing `reopen` transition.
- Does not call `advance_item`.
- Shows the operator the current state and a non-mutating recovery path.

---

## Notes for Claude

- **This is a read-only wrapper. Never mutate workflow state from this command.**
- `cancel` is a terminal transition, not a reopen substitute.
- Preserve terminal history; create follow-up work instead of rewriting terminal state unless the MCP schema adds an explicit reopen operation.
