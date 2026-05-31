---
description: "Reopen a terminal work-item (reopen trigger) back to queue — bypasses gates"
arguments: "<id-or-prefix>"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_context",
  "mcp__task-orchestrator__advance_item"
]
model: "claude-sonnet-4-5"
---

# /dx:reopen — Reopen a Terminal Work-Item (reopen trigger)

Send a `terminal` item back to `queue` and clear its `statusLabel`. Undoes a premature `/dx:complete` or `/dx:cancel`, or revives a container/series that was auto-terminalled by a cascade.

**Important:** `reopen` **bypasses gate enforcement** — the item re-enters `queue` regardless of note state. It does not delete existing notes (the proof-bundle, if any, remains filed).

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

- First positional → `<id-or-prefix>`. **Required.**

---

## Phase 2: Safety & Confirmation (MUTATES state)

**2a — Preflight.** `get_context(itemId="<id>")`. Read `role`, `statusLabel`.

**2b — Guard.**
- `role != "terminal"` → stop: "Item isn't terminal (role: `<role>`); nothing to reopen. To pause a live item use `/dx:block`."

**2c — Confirm + transition.** Note whether you're reviving a `done` or a `cancelled` item, then:
```
advance_item({ itemId: "<id>", trigger: "cancel", summary: "reopened via /dx:reopen" })  <!-- NOTE: reopen is not a valid trigger; use cancel then re-create, or verify schema -->
```
Result: TERMINAL → QUEUE, `statusLabel` cleared, gates bypassed on this hop.

---

## Phase 3: Render Result

```
↩️  Reopened: <title>   (terminal → queue)
   statusLabel cleared (was: <previous statusLabel or "—">)
   Note: gates were bypassed on reopen; existing notes (incl. proof-bundle) are retained.
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:start <id>     → advance it back into work
  /dx:context <id>   → review retained notes + gate status
  /dx:tree <parent>  → see it back among the parent's queue children
```

---

## Error Handling

**Item not found** / **not terminal** (handled in 2b) / **orchestrator unavailable**: report clearly; fall back to `advance_item({itemId, trigger:"cancel"})` directly.  <!-- reopen is not a valid trigger enum value -->

---

## Success Criteria

- ✅ Refuses non-terminal items with a clear redirect (`/dx:block` for pausing live work).
- ✅ Surfaces that gates are bypassed and notes are retained.
- ✅ Reports the cleared statusLabel.

---

## Notes for Claude

- **Mutates state.** `reopen` is the ONLY transition into `queue` from `terminal`, and the only one that bypasses gate enforcement — by design (you're reviving, not re-shipping).
- Common use: a long-running series/container auto-terminalled when its last non-terminal child completed. Reopen restores it to active so new children can be added. (This series uses `reopen` exactly this way after Phase-batch cascades.)
- Retained notes mean a reopened-then-recompleted item still satisfies the proof-bundle gate without re-filing — verify the bundle is still accurate before re-completing.
