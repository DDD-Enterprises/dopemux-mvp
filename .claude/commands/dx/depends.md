---
description: "Create a BLOCKS dependency between work-items (with linear/fan-out/fan-in shortcuts)"
arguments: "<from-id> <to-id> [--unblock-at queue|work|review|terminal]   |   --linear <id,id,...>   |   --fan-out <src-id> <id,id,...>   |   --fan-in <id,id,...> <target-id>"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__query_dependencies",
  "mcp__task-orchestrator__manage_dependencies"
]
model: "claude-sonnet-4-5"
---

# /dx:depends — Create a Dependency Edge

Wire up work-item dependencies so the orchestrator can compute blockers and auto-unblock.

**Direction (read carefully):** `/dx:depends <from> <to>` creates **`from` BLOCKS `to`** — i.e. `<to>` is blocked until `<from>` reaches its `unblockAt` role (default `terminal`). Mnemonic: *the first argument must finish before the second can proceed.*

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

Detect the mode from `$ARGUMENTS`:

- **Pairwise** (default): `<from-id> <to-id>` + optional `--unblock-at <role>` (default `terminal`). This wrapper creates `BLOCKS` edges only.
- **`--linear <id,id,id,...>`**: chain A→B→C→D (each blocks the next).
- **`--fan-out <src> <id,id,...>`**: `src` blocks each target (one prerequisite, many dependents).
- **`--fan-in <id,id,...> <target>`**: each source blocks `target` (many prerequisites, one dependent).

Pattern flags are mutually exclusive with pairwise args.

---

## Phase 2: Safety & Confirmation (this command MUTATES the dependency graph)

**2a — Echo the interpretation back before creating.** This is the direction footgun guard:
```
About to create:
  ⛔ <from title> BLOCKS <to title>
     → <to title> stays blocked until <from title> reaches "<unblock-at>".
```
For patterns, list every edge that will be created.

**2b — Idempotency check.** Dependency creation is **not** idempotent (you can create duplicate edges). Before creating, call:
```
query_dependencies(itemId="<from>", direction="outgoing", type="BLOCKS", includeItemInfo=true)
```
If an edge to `<to>` already exists, report it and skip (don't duplicate).

**2c — Create.**
- Pairwise:
  ```
  manage_dependencies(operation="create", dependencies=[
    { fromItemId: "<from>", toItemId: "<to>", type: "BLOCKS", unblockAt: "<unblock-at>" }
  ])
  ```
- Pattern (example linear):
  ```
  manage_dependencies(operation="create", pattern="linear", itemIds=["A","B","C"], unblockAt:"<role>")
  ```
The operation is **atomic**: cycle detection and duplicate detection apply across the whole batch — all succeed or all fail.

---

## Phase 3: Render Result

```
✅ Created <N> dependency edge(s):
  ⛔ <from title> (<short-prefix>) → blocks → <to title> (<short-prefix>)
       unblocks at: <unblock-at>
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:blocked              → see the new block reflected in the blocked list
  /dx:backlinks <to-id>    → what blocks <to>? (when wrapper ships; else query_dependencies direction=incoming)
  /dx:context <to-id>      → confirm <to> shows the dependency
```

---

## Error Handling

**Cycle detected** (atomic fail — nothing created):
```
❌ Dependency would create a cycle. No edges created (atomic).
   Review the chain with /dx:backlinks or query_dependencies(neighborsOnly=false).
```

**Duplicate** (caught in 2b or by the server): report the existing edge id; no-op.

**Item not found** / **orchestrator unavailable**: report clearly; for not-found, name which id failed to resolve.

---

## Success Criteria

- ✅ Direction interpreted and echoed before creation (no silent wrong-way edges).
- ✅ Existing edge detected and not duplicated.
- ✅ Cycle attempts fail atomically with a clear message.
- ✅ Pattern shortcuts (linear/fan-out/fan-in) produce the documented edge set.

---

## Notes for Claude

- **This command mutates the dependency graph.** Always echo the human-readable direction before creating — wrong-direction BLOCKS edges are a common, confusing mistake.
- `fromItemId` BLOCKS `toItemId`: the *from* item is the prerequisite; the *to* item is the dependent that waits.
- `unblockAt` default is `terminal` (dependent waits until prerequisite is fully done). Use `review` or `work` for looser coupling.
- Creation is atomic but **not idempotent** — always run the Phase 2b existence check first.
- This wrapper creates `BLOCKS` edges only (matches the plan's TP-CS-038 scope). For non-blocking `RELATES_TO` associations, call `manage_dependencies` directly — they have no gate effect and don't fit a "depends" mental model.
