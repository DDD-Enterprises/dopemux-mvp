---
description: "Search work-items by text + filters; optionally list notes for matched items"
arguments: "<query> [--tags csv] [--role queue|work|review|blocked|terminal] [--priority high|medium|low] [--limit N] [--offset N] [--with-notes]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__query_items",
  "mcp__task-orchestrator__query_notes"
]
model: "claude-sonnet-4-5"
---

# /dx:search — Find Work-Items by Text + Filters

Text search across work-item titles and summaries with optional filters. Pages through results in ADHD-friendly chunks. Optionally lists notes attached to matched items.

**Purpose**: bridge "I know what I want by description but not by ID" gap. Helps operators land on the right work-item without spelunking through `/dx:tree`.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

---

## Phase 1: Argument Parsing

First positional argument is the **query string** (text matched against title + summary).

Optional flags:

- `--tags <csv>` → tag filter (OR logic, substring match).
- `--role <state>` → restrict to one role: `queue`, `work`, `review`, `blocked`, or `terminal`.
- `--priority <high|medium|low>` → priority filter.
- `--limit N` → page size (default: 10 ADHD-friendly; max: 50).
- `--offset N` → page offset (default: 0).
- `--with-notes` → fetch notes for each matched item (headers only by default).

If no query string provided → print usage and exit.

---

## Phase 2: Fetch — Items

```
query_items({
  operation: "search",
  query: "<text>",
  tags: <if --tags>,
  role: <if --role>,
  priority: <if --priority>,
  limit: <N or 10>,
  offset: <N or 0>,
  sortBy: "modifiedAt",
  sortOrder: "desc"
})
```

Response shape: `{ items: [{ id, parentId, title, role, priority, depth, tags }], total, returned, limit, offset }`.

Recent edits surface first via `sortBy="modifiedAt" desc`.

---

## Phase 3: Fetch — Notes (only if `--with-notes`)

For each item in the result page, call:

```
query_notes(operation="list", itemId="<item-uuid>", includeBody=false)
```

Body is omitted by default for token efficiency; operator can inspect specific notes via `mcp__task-orchestrator__query_notes(operation="get", id="<note-uuid>", includeBody=true)`.

---

## Phase 4: Render

### Result cards

```
═══ Search: "<query>" — page <offset+1>..<offset+returned> of <total> ═══

▸ <title>  (<short-prefix>)
    Role: <role>  │  Priority: <priority>  │  Depth: <depth>
    Tags: <tags>
    <if --with-notes and item has notes:>
      Notes (<count>):
        • <key> [<role>]  (note <short-prefix>)
        • <key> [<role>]  (note <short-prefix>)

▸ <next match>
    ...
```

If `total === 0`:
```
ℹ️ No matches for "<query>".
  Try:
  - Broaden by removing --role / --priority / --tags filters
  - /dx:tree  to scan the workspace shape
  - /dx:next  to see the active queue instead
```

If more results exist beyond the current page:
```
… <total - (offset + returned)> more results. Page next via:
  /dx:search "<query>" --offset <offset + limit> [...same filters]
```

---

## Phase 5: ADHD-Friendly Footer

```
Next actions:
  /dx:context <id>        → see full item with gate status + notes
  /dx:tree <id>           → see this item's subtree
  /dx:next --tags ...     → pick the next work item matching these filters
```

---

## Error Handling

**Orchestrator MCP unavailable**:
```
⚠️ task-orchestrator MCP not responding.
  Fallback: query manually via mcp__task-orchestrator__query_items.
```

**Empty query**:
```
❌ Search query required.
  Usage: /dx:search "<text>" [--tags ...] [--role ...] [--priority ...] [--limit N] [--offset N] [--with-notes]
```

**Note search request**:
Currently the orchestrator does NOT expose full-text note search. `query_notes(operation="list")` only lists notes by `itemId`. The `--with-notes` flag fetches headers for already-matched items; it does NOT search within note bodies. If you need note-body search, fetch each note with `query_notes(operation="get", includeBody=true)` and grep locally.

---

## Success Criteria

- ✅ Query string required; helpful usage on empty input.
- ✅ Filters compose (tags AND role AND priority all narrow the result set).
- ✅ Default `limit=10` ADHD-friendly; explicit paging via `--offset`.
- ✅ Notes surface only when `--with-notes` requested.
- ✅ Empty result returns broadening suggestions.
- ✅ Output scannable in <10 seconds.

---

## Notes for Claude

- Two MCP tools used: `query_items` for the primary search; `query_notes` for optional note listing.
- `query_notes` has no `operation="search"` in this orchestrator version — only `get` and `list`. `--with-notes` therefore lists headers per matched item, not full-text-search across all notes.
- For the FTS-on-notes pattern operators may expect, fall back to: items hit → for each item call `query_notes(get, includeBody=true)` → grep client-side. Mention this in output footer if the operator is likely fishing.
- Page size capped at 50 (orchestrator default limit). Default 10 for first pass.
- Sort defaults: `modifiedAt desc` so recent edits surface first. Operator can override via raw MCP call if they need a different sort.
- This is a read-only wrapper. Never mutate workflow state from this command.
