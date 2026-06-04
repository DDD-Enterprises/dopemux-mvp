---
description: "Upsert a note on a work-item (gate-filling), or read a note by id"
arguments: "<id> <key> [--role queue|work|review]   |   read <note-id>"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_context",
  "mcp__task-orchestrator__manage_notes",
  "mcp__task-orchestrator__query_notes"
]
model: "claude-sonnet-4-5"
---

# /dx:note — Fill or Read a Work-Item Note

Two modes:

| Invocation | Mode | Wraps |
|---|---|---|
| `/dx:note <id> <key>` | **upsert** | `manage_notes(operation="upsert")` |
| `/dx:note read <note-id>` | **read** | `query_notes(operation="get")` |

Notes are how you satisfy schema gates (e.g. the `proof-bundle` complete-gate). The read mode closes the search→read loop: `/dx:search` returns snippets, `/dx:note read <id>` fetches the full body.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

Authoring reference: [`docs/03-reference/dx-command-authoring.md`](../../../docs/03-reference/dx-command-authoring.md).

---

## Phase 1: Mode Detection

Parse `$ARGUMENTS`:

- If the first token is `read` → **read mode**; second token is `<note-id>` (UUID).
- Else → **upsert mode**; first token is `<id-or-prefix>`, second is `<key>`. Optional `--role queue|work|review`.

If upsert mode is missing `<id>` or `<key>`, stop and ask (do not guess a key).

---

## Phase 2a: Upsert Mode (MUTATES state)

**Resolve the schema entry first.** Call `get_context(itemId="<id>")` and find the schema note whose `key` matches `<key>`. From it, read the expected `role`, `description`, `guidance`, and any `skill` pointer.

- If `--role` not given, use the role from the schema entry. If the key isn't in the schema and no `--role` is given, stop and ask for `--role` (free-form keys still need a phase).
- **If the schema entry has a `skill` pointer** (e.g. `pal:analyze`, `verify`): suggest running it and pasting the output as the body:
  ```
  💡 This note maps to skill "<skill>". Run it (e.g. mcp__pal__analyze) and paste the output,
     or write the note directly. Guidance:
     <guidance text>
  ```

**Body.** Use the operator-provided content. If none was provided inline, pre-populate a template from the schema `guidance` and ask the operator to fill/confirm before writing.

**Write** (idempotent on `(itemId, key)`):
```
manage_notes(operation="upsert", notes=[{ itemId: "<id>", key: "<key>", role: "<role>", body: "<body>" }])
```
If a note with this `(itemId, key)` already existed, say so — this was an **update**, not a create.

Render from the response `itemContext`:
```
✅ Note "<key>" (<role>) upserted on <title>.
   Note progress: <filled>/<total> required filled (remaining: <remaining>)
   <if guidancePointer: "Next unfilled required note: <guidancePointer>">
```

---

## Phase 2b: Read Mode (read-only)

```
query_notes(operation="get", id="<note-id>")
```
Render the full note:
```
── Note <key> (<role>) ──  id <short-prefix>
   item: <itemId>
   <full body>
```

---

## Phase 3: Footer

```
Next actions:
  /dx:context <id>      → see all notes + gate status on the item
  /dx:start <id>        → advance once required notes for the phase are filled
  /dx:complete <id>     → when proof-bundle (and all required notes) are filled
```

---

## Error Handling

**Item / note not found**:
```
❌ No <item|note> for "<input>". Try /dx:context <id> to list notes, or /dx:search.
```

**Missing key (upsert)**:
```
❌ Need a note key. See expected keys: /dx:context <id>
```

**Schema-less item** (no matching schema, `guidancePointer: null`): upsert still works with an explicit `--role`; warn that there is no gate guidance.

**Orchestrator MCP unavailable**: same fallback pattern as other `/dx:` commands (call the MCP tool directly).

---

## Success Criteria

- ✅ Mode picked correctly (read vs upsert).
- ✅ Upsert resolves the schema role/guidance/skill before writing.
- ✅ `(itemId, key)` collisions reported as updates (idempotent).
- ✅ Read mode returns the full body for a snippet found via `/dx:search`.
- ✅ Note progress / next-required surfaced after upsert.

---

## Notes for Claude

- **Upsert mutates state; read does not.**
- Upsert is idempotent on `(itemId, key)` — re-running overwrites the body, it does not create duplicates.
- The note's `role` must match the phase the schema assigns the key to (queue/work/review); mismatched roles file the note under the wrong phase and won't satisfy the intended gate.
- `proof-bundle` is role=`review` and is the mechanical complete-gate (per `AGENTS.md §9`). Filling it is what lets `/dx:complete` succeed.
- For PAL-chain keys (`analyze`/`planner`/`codereview`/`precommit`), the body should be the actual PAL tool output, not a paraphrase.
