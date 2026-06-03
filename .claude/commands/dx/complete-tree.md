---
description: "Complete (or cancel) a work-item subtree in one operation (complete_tree)"
arguments: "<id-or-prefix> [--cancel-incomplete] [--no-root]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__query_items",
  "mcp__task-orchestrator__complete_tree",
  "mcp__task-orchestrator__advance_item"
]
model: "claude-sonnet-4-5"
---

# /dx:complete-tree — Complete a Subtree (complete_tree)

Complete a work-item and all its descendants in one call, processed in topological (dependency) order. Use when shipping a feature whose children are all done.

**Best-effort, not all-or-nothing:** `complete_tree` completes every item whose gate passes; items missing a required note are reported with `gateErrors`, and their dependents are `skipped`. It does NOT abort the whole operation on the first failure.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

- First positional → `<id-or-prefix>` (the subtree root). **Required.**
- `--no-root` → complete only descendants, leave the root open (`includeRoot=false`). Default: root is completed last.
- `--cancel-incomplete` → after the complete pass, cancel the items that couldn't complete (gate failures / skipped), instead of leaving them open.

---

## Phase 2: Safety & Confirmation (MUTATES many items; CASCADES)

**2a — Preflight.** `query_items(operation="overview", itemId="<id>")` → show the subtree: child counts by role, which children are still non-terminal. Surface how many items will be affected.

**2b — Confirm.** This is a bulk, irreversible-feeling operation. Show the count and confirm before proceeding:
```
About to complete <N> items under <title> (topological order<, root included | root excluded>).
```

**2c — Complete pass.**
```
complete_tree({ itemId: "<id>", trigger: "complete" })
```
Each result: `applied` / `skipped` (skippedReason) / `gateErrors` (missing notes). Already-terminal items report as skipped.

**2d — `--cancel-incomplete` follow-up (only if flag set).** Collect the ids that have `gateErrors` or were `skipped` for a non-terminal reason (exclude already-terminal). Cancel each **individually** so already-completed descendants are left untouched:
```
advance_item({ itemId: "<failed id>", trigger: "cancel", summary: "cancel incomplete item after /dx:complete-tree" })
```
**Do NOT** re-run `complete_tree(trigger="cancel")` on these — as a tree operation it would cascade-cancel descendants that already completed successfully. Per-item `advance_item` cancels only the named items.

---

## Phase 3: Render Result

```
🌳 complete-tree on <title>

Completed (<summary.completed>):
  ✅ <title> (<short-prefix>)
Skipped (<summary.skipped>):
  ⏭️  <title> — <skippedReason>
Gate failures (<summary.gateFailures>):
  ⚠️ <title> — <gateErrors joined>   → fill via /dx:note <prefix> <key>

<if --cancel-incomplete ran:>
  🚫 Cancelled <K> incomplete item(s).
```

If gate failures remain and `--cancel-incomplete` was NOT passed, tell the operator: fill the missing notes (`/dx:note`) then re-run, or re-run with `--cancel-incomplete` to abandon them.

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:tree <id>      → confirm the subtree state after the operation
  /dx:note <id> <key>→ fill a gate that blocked completion
  /dx:reopen <id>    → inspect an over-completed parent; automatic reopen is not currently exposed
```

---

## Error Handling

**Item not found** / **orchestrator unavailable**: report clearly. **Empty subtree** (no descendants): with `--no-root` there's nothing to do; without it, this degenerates to a single-item complete — suggest `/dx:complete <id>` instead.

---

## Success Criteria

- ✅ Subtree previewed + affected count confirmed before mutating.
- ✅ Results split into completed / skipped / gate-failed (best-effort semantics surfaced, not "all-or-nothing").
- ✅ `--cancel-incomplete` resolves leftovers; default leaves them open with guidance.
- ✅ `--no-root` leaves the root open.

---

## Notes for Claude

- **This command mutates many items and cascades.** Always preflight + confirm; the blast radius is the whole subtree.
- `complete_tree` is best-effort and gate-aware: it completes what it can in topological order and reports the rest. There is no hard abort — read the `summary` to know what actually happened.
- `includeRoot` defaults true (root completed last). Use `--no-root` to ship children but keep the parent active (common for long-running containers/series — avoids the auto-terminal-then-reopen dance).
- For a single item, prefer `/dx:complete <id>` (clearer proof-bundle gate UX).
