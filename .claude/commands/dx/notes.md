---
description: "List all notes on a work-item (query_notes list) — read-only"
arguments: "<item-id-or-prefix> [--role queue|work|review] [--no-body]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__query_notes"
]
model: "claude-sonnet-4-5"
---

# /dx:notes — List Notes on a Work-Item (read-only)

Show every note filed on an item — the filled gates, PAL-chain outputs, proof bundle, etc. The list companion to `/dx:note read <noteId>` (which fetches one note by id) and `/dx:note <id> <key>` (which upserts).

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Argument Parsing

- First positional → `<item-id-or-prefix>`. **Required.**
- `--role <queue|work|review>` → filter to one phase (default: all phases).
- `--no-body` → omit note bodies (headers only) for a fast, token-light scan.

---

## Phase 2: Fetch

```
query_notes({
  operation: "list",
  itemId: "<id>",
  role: <if --role provided>,
  includeBody: <false if --no-body, else true>
})
```
Returns `{ notes: [...], total: N }`.

---

## Phase 3: Render

```
🗒️  Notes on <item short-prefix>  (<total> total<, role=<role>> if filtered)

<for each note:>
  ── <key>  (<role>)  ── note id <short-prefix>
  <if includeBody: the body; else: "(body omitted — /dx:note read <note-prefix>)">
```

If `total === 0`:
```
No notes filed<, for role <role>> if filtered. See expected notes: /dx:context <id>
```

---

## Phase 4: ADHD-Friendly Footer

```
Next actions:
  /dx:note read <note-id>  → full body of one note (when listed with --no-body)
  /dx:note <id> <key>      → fill or update a note
  /dx:context <id>         → gate status + which required notes are still missing
```

---

## Error Handling

**Item not found** / **orchestrator unavailable**: report clearly; fall back to `query_notes(operation="list", itemId=...)` directly.

---

## Success Criteria

- ✅ Lists all notes (or one phase with `--role`).
- ✅ `--no-body` gives a scannable header-only view with read pointers.
- ✅ Empty result points at `/dx:context` for the expected-notes schema.

---

## Notes for Claude

- **This is a read-only wrapper. Never mutate workflow state from this command.**
- This is the **list** half of note reading; the single-note **get** is `/dx:note read <noteId>` (already in `note.md`). `/dx:search` finds notes by text; `/dx:notes` lists everything on a known item.
- Default `includeBody=true`; reach for `--no-body` on items with large notes (e.g. a full proof bundle) when you just want the inventory.
