---
description: "Advance a work-item to its next role (start trigger) after a gate check"
arguments: "<id-or-prefix> [--summary <text>]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_context",
  "mcp__task-orchestrator__advance_item"
]
model: "claude-sonnet-4-5"
---

# /dx:start — Advance a Work-Item (start trigger)

Move an item one step forward in its lifecycle: `queue → work → review → terminal`. Gate-checked first so you never transition into a phase whose required notes are unfilled.

**Purpose**: the "I'm picking this up" / "this phase is done, move on" action — without hand-writing `advance_item`.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

Parse `$ARGUMENTS`:

- First positional → `<id-or-prefix>` (UUID or ≥4-hex prefix). **Required.**
- `--summary <text>` → human reason for the transition (optional). See actor note below.

If no id is given, stop and ask for one (do not guess).

---

## Phase 2: Safety & Confirmation (this command MUTATES state)

**2a — Preflight read.** Call `get_context(itemId="<id>")`. Capture: `role`, `statusLabel`, `canAdvance`, missing required notes, `noteProgress`, `guidancePointer`.

**2b — Gate check.** 
- If `role == "terminal"` -> stop: "Already terminal; nothing to start. `/dx:reopen <id>` can inspect the item, but the current MCP schema does not expose a reopen transition."
- If `role == "blocked"` → stop: "Item is blocked; `start` is not valid from blocked. Resume it with `/dx:resume <id>`."
- If `canAdvance == false` → **do not transition.** Show the missing required notes and stop:
  ```
  ⚠️ Cannot start <title> — gate not satisfied.
     Current phase: <role>
     Missing required notes: <comma-list>
     Fill them: /dx:note <short-prefix> <key>
     Then re-run /dx:start.
  ```
- If `canAdvance == true` → show the transition that will happen and proceed:
  ```
  ▸ <title> (<short-prefix>): <role> → <next-role>   [start]
  ```

**2c — Transition.** Call:
```
advance_item({ itemId: "<id>", trigger: "start", summary: "<--summary or 'start via /dx:start'>" })
```

> **No `actor` field.** `advance_item` accepts only `{itemId, trigger, summary?}`. To attribute the transition today, include your actor id in `--summary` (Dopemux convention `worktree-<basename>-<branch>`). Structured actor attribution awaits `claim_item`.

---

## Phase 3: Render Result

From the `results[0]` object:

```
✅ Started: <title>
   <previousRole> → <newRole>   (trigger: start)

Next phase: <newRole>
  Note progress: <filled>/<total> required filled (remaining: <remaining>)
  Guidance: <guidancePointer or "— (all required filled / no schema)">
  Expected notes for <newRole>:
    [✓|✗] <key> (<required ? "required" : "optional">) — <description>
```

If `cascadeEvents` non-empty (a parent auto-advanced), surface them:
```
↑ Cascade: <parent title> <previousRole> → <targetRole>
```
If `unblockedItems` / `allUnblockedItems` non-empty:
```
🔓 Unblocked: <title> (<short-prefix>)
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:note <id> <key>   → fill a note for the new phase
  /dx:context <id>      → re-check gate status
  /dx:complete <id>     → when all required notes (esp. proof-bundle) are filled
```

---

## Error Handling

**Item not found**:
```
❌ No item for "<input>". Try /dx:next, /dx:tree, or query_items search.
```

**Orchestrator MCP unavailable**:
```
⚠️ task-orchestrator MCP not responding.
  Fallback: mcp__task-orchestrator__advance_item(itemId, trigger:"start") after a manual get_context gate check.
```

**Gate failure on the actual call** (race: notes changed between preflight and transition): report the orchestrator's `expectedNotes`/error verbatim; do not retry blindly.

---

## Success Criteria

- ✅ Preflight gate check runs before any mutation.
- ✅ Unsatisfied gate stops the command with the exact missing notes — no transition.
- ✅ Successful transition reports old→new role + next-phase guidance.
- ✅ Cascades and unblocks surfaced.
- ✅ Scannable in <10s.

---

## Notes for Claude

- **This command mutates workflow state.** Always do the Phase 2 preflight; never transition blind.
- `start` is multi-hop: repeated calls walk `queue → work → review → terminal`. Each hop re-checks that phase's required notes.
- The `Actor:` field in `/dx:context` session-resume will show `—` for these transitions until `claim_item` ships — expected, not a bug.
- Use `summary` for the human reason; it is the only free-text field `advance_item` accepts.
