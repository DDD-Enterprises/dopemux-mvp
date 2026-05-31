---
description: "Pause a work-item (block trigger) — saves its current role for later resume"
arguments: "<id-or-prefix> [reason]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_context",
  "mcp__task-orchestrator__advance_item"
]
model: "claude-sonnet-4-5"
---

# /dx:block — Pause a Work-Item (block trigger)

Move an item to `blocked`, saving its current role so `/dx:resume` can restore it. Use when work is paused on an external dependency or operator decision.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

- First positional → `<id-or-prefix>`. **Required.**
- Remaining text → optional `reason` (becomes the transition `summary`).

---

## Phase 2: Safety & Confirmation (MUTATES state)

**2a — Preflight.** `get_context(itemId="<id>")`. Read `role`.

**2b — Guard.**
- `role == "terminal"` → stop: "Terminal items can't be blocked. Use `/dx:reopen <id>` first if you need to revive it."
- `role == "blocked"` → stop: "Already blocked. Use `/dx:resume <id>` to restore it."

**2c — Confirm + transition.** Show what will pause, then:
```
advance_item({ itemId: "<id>", trigger: "block", summary: "<reason or 'blocked via /dx:block'>" })
```
The orchestrator saves `previousRole` automatically so `resume` can restore it.

> No `actor` param — attribution rides in `summary` (see authoring reference).

---

## Phase 3: Render Result

```
⛔ Blocked: <title>   (<previousRole> → blocked)
   Saved role: <previousRole>  (restored by /dx:resume)
   Reason: <summary or "—">
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:resume <id>   → unblock and restore the saved role
  /dx:blocked       → see everything blocked
  /dx:next          → pick something else to work
```

---

## Error Handling

**Item not found** / **already terminal or blocked** (handled in 2b) / **orchestrator unavailable**: report clearly; for the unavailable case, fall back to `advance_item({itemId, trigger:"block"})` directly.

---

## Success Criteria

- ✅ Preflight role read before mutating.
- ✅ Terminal/blocked items rejected with the right redirect.
- ✅ `previousRole` preserved for `/dx:resume`.
- ✅ Reason captured in the transition summary.

---

## Notes for Claude

- **Mutates state.** `block` and `hold` both land in `blocked`; this wrapper uses `block` (operator-initiated pause). Both save `previousRole`.
- Blocking is reversible — `/dx:resume` returns the item to exactly its saved role.
- A dependency-driven block (auto, via a BLOCKS edge) is different: it shows in `/dx:blocked` as `blockType="dependency"` and clears automatically. This command creates an `explicit` block.
