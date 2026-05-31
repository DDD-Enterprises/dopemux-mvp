---
description: "Pick the next task-orchestrator work item with ADHD-aware ranking"
arguments: "[--tags <comma-list>] [--priority high|medium|low] [--scope <ancestor-uuid>] [--limit N]"
allowed-tools: [
  "Bash", "Read",
  "mcp__task-orchestrator__get_next_item",
  "mcp__task-orchestrator__get_context",
  "mcp__conport__get_active_context"
]
model: "claude-sonnet-4-5"
---

# /dx:next — Pick the Next Work Item

Surface up to N unblocked queue items ranked by priority (high → low) then complexity (low → high — quick wins first), with ADHD-aware breadcrumbs and ancestor chains.

**Purpose**: replace "what should I work on?" friction. One call → top candidates with everything needed to decide.

**Authority**: task-orchestrator MCP per `AGENTS.md §6` + ADR `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`.

---

## Phase 1: Argument Parsing

Parse `$ARGUMENTS` for optional filters:

- `--tags <comma-list>` → pass to `tags` parameter (OR logic, substring match)
- `--priority <level>` → pass to `priority` parameter (high/medium/low)
- `--scope <uuid>` → pass to `parentId` parameter (scope to subtree)
- `--limit N` → limit display to N results client-side (default: 3 for ADHD-friendly disclosure; max: 10)

Default if no arguments: display top 3 results from returned list.

---

## Phase 2: Fetch Candidates

Call `mcp__task-orchestrator__get_next_item` with parsed parameters (parentId, role, priority, tags only).

```
get_next_item({
  tags: <if provided>,
  priority: <if provided>,
  parentId: <if provided>
})
```

The orchestrator returns up to N unblocked queue items, ranked by priority (high first) then complexity (low first).

---

## Phase 3: Display Results

For each returned item, render a card:

```
┌─ Candidate <N>: <title> ────────────────────────────
│  ID:          <short-prefix> (full: <full-uuid>)
│  Priority:    <priority>  │  Complexity: <complexity or "—">
│  Tags:        <comma-list>
│  Ancestors:   <root-title> > <feature-title> > ...
│                (so you can see where this lives)
│  Schema:      <schema-key from get_context if loaded>
│  Gate:        canAdvance=<true|false>; missing=<list>
│  Guidance:    <guidancePointer or "—">
└─────────────────────────────────────────────────────
```

If no parent or ancestor context is present in the returned item, show "(top-level)" instead of a breadcrumb.

If the orchestrator returns 0 candidates, print:

```
✅ Queue is empty for these filters.
  Try:
  - /dx:tree    to see container overview
  - /dx:blocked to see what's waiting on dependencies
  - /dx:next --priority medium  to broaden
```

---

## Phase 4: ADHD-Friendly Footer

After the cards, print:

```
ADHD note: high-priority items are listed first, then ranked by
LOW complexity (quick wins first) within the priority band. Pick the
top candidate unless your energy/focus calls for something else.

Next actions:
  /dx:context <id>       → see full gate status + missing notes
  /dx:start <id>         → claim + advance to work (when wrapper ships)
  /dx:next --limit 10    → see more candidates
```

---

## Phase 5: ConPort Cross-Check (Optional)

If `mcp__conport__get_active_context` is available, fetch it and look for `current_focus`. If set and matches one of the candidates, mark that candidate with a `(resuming previous focus)` annotation.

This bridges interrupted sessions — the operator's prior intent surfaces alongside the next-best ranking.

---

## Error Handling

**Orchestrator MCP unavailable**:
```
⚠️ task-orchestrator MCP not responding.
  Check: ls /Users/hue/plugins/dopemux-mission-control/scripts/
  Or restart your Claude Code session.
  Fallback: query manually via mcp__task-orchestrator__get_next_item.
```

**No matching schema for any candidate** (schema-less mode):
```
ℹ️  Items advance schema-less. canAdvance always true; guidancePointer null.
  To enable guidance: ensure .taskorchestrator/config.yaml exists at repo root
  and restart MCP (see docs/03-reference/systems/task-orchestrator/).
```

---

## Success Criteria

- ✅ Top N candidates displayed with breadcrumbs
- ✅ Each card shows enough info to decide (priority, complexity, schema, gate, guidance)
- ✅ Empty queue produces helpful next-action suggestions
- ✅ ConPort cross-check surfaces continuity when available
- ✅ Output is scannable in <10 seconds (ADHD-friendly disclosure)

---

## Notes for Claude

- Default to limit=3 (ADHD-friendly).
- Show full UUIDs ONCE per card (small font / parenthetical). Short prefix is what operators will type.
- If multiple items share priority, rank by complexity ascending (workflow guide §1 default).
- Use `--scope <uuid>` when the operator is heads-down in one feature; otherwise show the global queue.
