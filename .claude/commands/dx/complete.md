---
description: "Complete a work-item (complete trigger) after verifying the proof-bundle gate"
arguments: "<id-or-prefix> [--summary <text>]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_context",
  "mcp__task-orchestrator__advance_item"
]
model: "claude-sonnet-4-5"
---

# /dx:complete — Complete a Work-Item (complete trigger)

Drive an item to `terminal`. The orchestrator enforces the complete-gate: **all required notes across all phases must be filled** — for `task-packet` items that means the `proof-bundle` note (per `AGENTS.md §9`: no proof means incomplete).

**Purpose**: ship a work-item with its proof intact, and surface what the completion cascades/unblocks.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

Parse `$ARGUMENTS`:

- First positional → `<id-or-prefix>`. **Required.**
- `--summary <text>` → human reason / actor id for the transition (optional).

---

## Phase 2: Safety & Confirmation (this command MUTATES state, and can CASCADE)

**2a — Preflight.** `get_context(itemId="<id>")`. Capture `role`, `canAdvance`, missing required notes, `noteProgress`.

**2b — Proof-bundle gate.**
- If `canAdvance == false` (proof-bundle or other required note missing) → **do not transition.** Stop:
  ```
  ⚠️ Cannot complete <title> — required notes missing: <comma-list>
     The proof-bundle is the complete-gate (AGENTS.md §9). Fill it:
       /dx:note <short-prefix> proof-bundle
     Required fields: TP id/path · worktree path · branch · repo identity ·
       slices · files changed (with line counts) · validations PASS/FAIL/NOT_RUN ·
       codereview status · precommit status · commit SHA · PR URL/blocker ·
       residual risks · UNKNOWNs · cleanup status.
  ```
  Optionally offer to assemble the proof-bundle from this session's evidence (files changed, commit SHA, validation results) and write it via `/dx:note` — but the operator confirms before it's filed.

**2c — Cascade warning.** If this item has a parent and is (or may be) the parent's last non-terminal child, warn:
```
⚠️ Completing this may auto-complete its parent <parent title> (cascade).
   For a long-running container/series this can be a false "done" — reopen the parent
   afterward if more work remains.
```
Confirm before proceeding.

**2d — Complete.**
```
advance_item(transitions=[{ itemId: "<id>", trigger: "complete", summary: "<--summary or 'complete via /dx:complete'>" }])
```
> No `actor` field — use `summary` (see authoring reference). The `Actor:` field in session-resume stays `—` until `claim_item` ships.

---

## Phase 3: Render Result

```
✅ Completed: <title>   (<previousRole> → terminal)

<if cascadeEvents non-empty:>
  ↑ Cascade:
    <parent title>: <previousRole> → <targetRole>  (statusLabel: <statusLabel>)
<if allUnblockedItems / unblockedItems non-empty:>
  🔓 Unblocked by this completion:
    • <title> (<short-prefix>)
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:next                 → pick the next unblocked item
  /dx:tree <parent-id>     → see the parent's remaining children
  /dx:context <unblocked>  → inspect a newly-unblocked item
```

---

## Error Handling

**Gate failure (missing proof-bundle)** — handled in Phase 2b (stop, don't transition).

**Item not found** / **already terminal** / **orchestrator unavailable**: report clearly; for already-terminal, no-op with a note that nothing changed.

**Gate failure on the actual call** (notes changed mid-flight): surface the orchestrator's `expectedNotes` verbatim; do not retry blindly.

---

## Success Criteria

- ✅ Proof-bundle (and all required notes) verified before any mutation.
- ✅ Missing gate stops the command with the exact missing keys + proof-bundle field list.
- ✅ Cascade warned about before completing; cascade events surfaced after.
- ✅ Unblocked items listed so the operator knows what's now actionable.

---

## Notes for Claude

- **This command mutates state and can cascade.** Completing the last non-terminal child auto-terminals the parent — intended for leaf containers, a false "done" for long-running series. Reopen the parent if more phases remain.
- The complete-gate is mechanical and server-enforced; this command surfaces it early but never bypasses it. There is no `--force`.
- Proof-bundle structure is `AGENTS.md §9`; the bundle goes *into* the note (per `AGENTS.md §12`), not just attached to a PR.
- Actor attribution: `summary` only (no `actor` param on `advance_item`).
