---
description: "Cancel a work-item (cancel trigger) — sends it to terminal with statusLabel=cancelled"
arguments: "<id-or-prefix> [reason]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_context",
  "mcp__task-orchestrator__advance_item"
]
model: "claude-sonnet-4-5"
---

# /dx:cancel — Cancel a Work-Item (cancel trigger)

Send an item to `terminal` with `statusLabel = "cancelled"` — abandoned, not completed. Bypasses the proof-bundle gate (cancelling is not shipping). Reversible via `/dx:reopen`.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

- First positional → `<id-or-prefix>`. **Required.**
- Remaining text → optional `reason` (becomes the transition `summary`). Strongly encouraged — say *why* it's abandoned.

---

## Phase 2: Safety & Confirmation (MUTATES state; can CASCADE)

**2a — Preflight.** `get_context(itemId="<id>")`. Read `role`, `title`, and whether it has children.

**2b — Guard.**
- `role == "terminal"` → stop: "Already terminal. Nothing to cancel."

**2c — Cascade warning.** If this item is (or may be) the parent's last non-terminal child, warn:
```
⚠️ Cancelling this may auto-terminal its parent <parent title> (cascade).
   If the parent is a long-running container/series, reopen it afterward.
```
If the item itself has non-terminal children, warn that they are NOT auto-cancelled — cancel them individually first. (A one-shot `/dx:complete-tree <id> --cancel-incomplete` is planned in TP-CS-043 but not yet shipped.)

**2d — Confirm (required) + transition.** Cancellation is a deliberate abandonment — confirm before acting, then:
```
advance_item({ itemId: "<id>", trigger: "cancel", summary: "<reason or 'cancelled via /dx:cancel'>" })
```

> No `actor` param — attribution rides in `summary`.

---

## Phase 3: Render Result

```
🚫 Cancelled: <title>   (<previousRole> → terminal, statusLabel=cancelled)
   Reason: <summary or "—">

<if cascadeEvents:>
  ↑ Cascade: <parent title> <previousRole> → <targetRole>
<if unblockedItems:>
  🔓 Unblocked: <title> (<short-prefix>)   (a dependency on the cancelled item cleared)
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:reopen <id>   → changed your mind? send it back to queue
  /dx:tree <parent> → check the parent's remaining children
  /dx:next          → pick the next item
```

---

## Error Handling

**Item not found** / **already terminal** (handled in 2b) / **orchestrator unavailable**: report clearly; fall back to `advance_item({itemId, trigger:"cancel"})` directly.

---

## Success Criteria

- ✅ Preflight + explicit confirm before the irreversible-feeling action.
- ✅ Cascade and child-handling warned about before cancelling.
- ✅ `statusLabel=cancelled` distinguishes it from a completed item.
- ✅ Reason captured.

---

## Notes for Claude

- **Mutates state and can cascade.** `cancel` differs from `complete`: cancel → `statusLabel=cancelled` and bypasses the proof-bundle gate; complete → `done` and enforces proof. Use cancel for abandoned work, complete for shipped work.
- Reversible: `/dx:reopen` returns a cancelled item to `queue` and clears the label.
- Cancelling the last non-terminal child auto-terminals the parent (observed orchestrator behavior) — reopen long-running parents afterward.
