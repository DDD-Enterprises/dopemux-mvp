# Sprint Management Module (mem4sprint)

**Module Version**: 2.0.0 (post-orchestrator-authority reconciliation, TP-CS-023)
**Framework**: mem4sprint — ADHD-optimized sprint **methodology**, now backed by task-orchestrator (workflow) + ConPort (decisions/observations).
**Modes**: PLAN/ACT mode-aware via ConPort `active_context`.
**Authority Layer**: This file documents the *methodology*. Canonical authority for *what each system owns* lives in [authority-matrix.md](../coordination/authority-matrix.md).

> **What changed in 2.0**: Sprint workflow entities (goals, subtasks, stories, epics, bugs, retrospectives) moved from ConPort `custom_data` / `progress_entry` into **task-orchestrator work-items** under the `sprint-goal` (lifecycle PERMANENT) and related schemas per the accepted [adr-task-orchestrator-as-workflow-authority](../../../docs/90-adr/adr-task-orchestrator-as-workflow-authority.md). ConPort still owns decisions, knowledge-graph genealogy, active_context, and non-workflow observations (risk, sprint metrics). The mem4sprint **name is retained** as a methodology brand; the storage backend has shifted.

---

## Authority & Boundary Alignment

This file **IS** the operator-facing methodology guide for ADHD-friendly sprint structure on Dopemux.

This file **IS NOT** the source of truth for:

| Topic | Canonical source |
|---|---|
| System authority boundaries | [authority-matrix.md](../coordination/authority-matrix.md) |
| Orchestrator MCP operations (notes, schemas, gates) | [.claude/CLAUDE.md §Orchestrator Operations](../../CLAUDE.md) + [orchestrator-note-filling-protocol.md](../../../docs/03-reference/orchestrator-note-filling-protocol.md) |
| Workflow event payloads | [event-patterns.md](event-patterns.md) |
| `sprint-goal` / `retrospective` schema definitions | [.taskorchestrator/config.yaml](../../../.taskorchestrator/config.yaml) |
| `/sc:` vs `/dx:` command surfaces and shipping status | [superclaude-workflows.md](superclaude-workflows.md) |
| PAL chain & proof-bundle complete-gate | [AGENTS.md §5 + §9](../../../AGENTS.md) |
| ADHD engine internals (energy, breaks, focus sessions) | [adhd-patterns.md](adhd-patterns.md) |

If something here contradicts a canonical source, the canonical source wins.

---

## Entity Mapping (mem4sprint → current architecture)

All workflow entities live in **task-orchestrator**. ConPort retains decisions and observations only.

| mem4sprint entity | Canonical store | Schema / mechanism | Notes |
|---|---|---|---|
| `sprint_goal` | task-orchestrator | schema `sprint-goal`, `lifecycle: PERMANENT` | One root work-item per sprint. Required note: `goal-definition`. |
| `sprint_subtask` | task-orchestrator | schema `task-packet`, `parentId` = sprint goal | Standard repo-changing work; proof-bundle gate enforced. |
| `story`, `epic` | task-orchestrator | schema `feature-implementation` | Multi-TP feature container under the sprint goal. |
| `bug` | task-orchestrator | schema `bug-fix` | Workflow-managed. |
| `retrospective` / `retrospective_item` | task-orchestrator | schema `retrospective`, `lifecycle: AUTO` | Required notes: `scope`, `observations`, `findings`. Phase 6 / TP-CS-120. |
| `blocker` (intra-workflow) | task-orchestrator | `BLOCKED` role + `manage_dependencies(BLOCKS)` | Resolves automatically when blocker reaches `unblockAt` role. |
| `blocker` (external / systemic) | ConPort | `log_decision` (tag: `blocker`, severity field) | Cross-domain; not a workflow transition. |
| `risk` | ConPort | `custom_data` (category: `sprint_risks`) | Observation, not workflow. |
| `sprint_metric` | ConPort | `custom_data` (category: `sprint_metrics`) | Observation, not workflow. |
| `decision` | ConPort | `log_decision` | **Unchanged** — canonical decision authority. |
| `artifact` | commit + proof-bundle note | not its own type | Commit SHA + files in proof-bundle. |
| `test` | proof-bundle validation entry + commit | not its own type | Validation results live in the `proof-bundle` note (PASS/FAIL/NOT_RUN buckets). |

### Migrating legacy ConPort sprint `custom_data`

For pre-2.0 sprint entities still in ConPort `custom_data`: (1) inventory via `search_custom_data_value_fts`; (2) re-create as orchestrator work-items with the correct `type` + tags; (3) update related ConPort decisions per the cross-domain convention below (orchestrator UUID stored in `implementation_details` or via a `custom_data` shadow entry); (4) keep the legacy entry for audit (don't delete). No automated bridge ships in this packet — see [adr-task-orchestrator-claude-surface-integration](../../../docs/90-adr/adr-task-orchestrator-claude-surface-integration.md) future work.

---

## Sprint Lifecycle

### 1. Open the sprint

Create the sprint-goal work-item. Required note `goal-definition` (Sprint ID, goal sentence, linked stories, definition of done) gates the start transition.

```
manage_items(operation="create", items=[{
  title: "Sprint S-2026.05: <one-line goal>",
  type: "sprint-goal",
  tags: "sprint,S-2026.05",
  priority: "high"
}])
# → returns work-item UUID, say <goal-uuid>

manage_notes(operation="upsert", notes=[{
  itemId: "<goal-uuid>",
  key: "goal-definition",
  role: "queue",
  body: "Sprint S-2026.05. Goal: <statement>. Linked stories: ... Definition of done: ..."
}])

advance_item(transitions=[{itemId: "<goal-uuid>", trigger: "start"}])
# sprint-goal → work
```

### 2. Populate with subtasks / stories

Use `create_work_tree` to scaffold children under the sprint goal — see [PRD Decomposition Flow](#prd-decomposition-flow) below.

### 3. Run the sprint

Standard workflow per [superclaude-workflows.md §Primary Development Flow](superclaude-workflows.md): `/dx:next` → start → work → proof-bundle → complete. Each subtask cascade is independent.

### 4. Retrospective

Spin a `retrospective` work-item (schema `retrospective`, lifecycle AUTO). Required notes: `scope`, `observations`, `findings`. Retro reaches terminal when its required-action children are themselves terminal (per `retrospective-actions` trait).

### 5. Close the sprint (PERMANENT lifecycle semantics)

`sprint-goal` has `lifecycle: PERMANENT` — **no auto-cascade**. Operator closes the sprint explicitly:

- **Completed sprint**: confirm all child work-items are `terminal`; file `progress-summary` (work-phase, optional but recommended) as a closure record; once the retrospective work-item is also `terminal`, `advance_item(trigger="complete")` on the sprint goal. The sprint-goal schema does **not** define a `proof-bundle` note — each subtask (task-packet / bug-fix / feature-implementation) carries its own per AGENTS.md §9. Sprint closure rolls up child proofs plus a ConPort decision summarizing outcome.
- **Abandoned sprint**: `advance_item(trigger="cancel")` — `statusLabel` becomes `cancelled`.

The PERMANENT lifecycle is deliberate: sprints stay queryable indefinitely as audit anchors for their child work.

---

## PLAN/ACT Mode Management

ConPort `active_context` retains authority for **mode and focus tracking** (not workflow state). This stays unchanged.

```bash
# PLAN mode (architecture, sprint planning, story breakdown)
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" \
  --patch_content '{"mode": "PLAN", "sprint_id": "S-2026.05", "focus": "Sprint planning"}'

# ACT mode (implementation, debugging, testing)
mcp__conport__update_active_context --workspace_id "/Users/hue/code/dopemux-mvp" \
  --patch_content '{"mode": "ACT", "current_item": "<work-item-uuid>", "focus": "Implementation"}'
```

The mode value is a hint for the operator and downstream tooling (hooks, ADHD engine). It does **not** drive orchestrator transitions.

---

## PRD Decomposition Flow

Canonical path from PRD to orchestrator state:

```
1. /dx:prd-parse <prd-path>
     └─> PAL planner generates structured JSON breakdown

2. Human review
     └─> Operator approves/edits JSON before any orchestrator write

3. create_work_tree (per story; call once per story)
     └─> mcp__task-orchestrator__create_work_tree(
           parentId: "<sprint-goal-uuid>",            # existing sprint goal
           root: { title: "Story: <name>",
                   type: "feature-implementation",   # drives schema selection
                   tags: "story" },
           children: [                                # siblings at root.depth+1
             { ref: "t1", title: "Subtask: <…>",
               type: "task-packet", tags: "subtask" },
             { ref: "t2", title: "Subtask: <…>",
               type: "task-packet", tags: "subtask" }
           ],
           deps: [                                    # optional intra-story BLOCKS
             { from: "t2", to: "t1", type: "BLOCKS",
               unblockAt: "review" }
           ]
         )

4. ConPort log_decision (optional but recommended)
     └─> Capture the PRD-decomposition decision; link_conport_items → sprint-goal UUID
```

One `create_work_tree` call creates **one root + its direct children only** (depth cap < 3); call once per story for multi-story sprints. The `type` field on each item drives schema activation (and gate enforcement); tag-only items fall through to the `default` schema. `ref` is a local handle for `deps` wiring within the same call (response returns real UUIDs). PAL (`pal/planner`) is the canonical reasoning surface. Human review is non-negotiable: orchestrator writes only happen after approval.

---

## Sprint Query Patterns

### Workflow entities (orchestrator)

```
# All items under a sprint goal
query_items(operation="overview", itemId="<sprint-goal-uuid>")

# Subtasks in active states
query_items(operation="search",
  parentId="<sprint-goal-uuid>",
  role="work")

# Next ADHD-ranked item under this sprint
get_next_item(parentId="<sprint-goal-uuid>", limit=3, includeAncestors=true)

# Blocked subtree
get_blocked_items(parentId="<sprint-goal-uuid>", includeItemDetails=true)
```

### Decisions, risks, metrics (ConPort)

```bash
mcp__conport__search_decisions_fts --query_term 'tags:"sprint" tags:"S-2026.05"'
mcp__conport__search_custom_data_value_fts --query_term 'value_text:"sprint_id:S-2026.05" value_text:"category:sprint_risks"'
mcp__conport__get_custom_data --category sprint_metrics --key "S-2026.05_velocity"
```

---

## ADHD Optimizations

### Visual sprint progress

Counts come straight from `query_items` child-role totals (no manual roll-up):

```
sprint_overview = query_items(operation="overview", itemId="<sprint-goal-uuid>")
# sprint_overview.childCounts: { queue: N, work: N, review: N, blocked: N, terminal: N }
# Render as: [████░░░░] terminal/total complete ✅
```

### Next action recommendation

```
get_next_item(parentId="<sprint-goal-uuid>", limit=3, includeAncestors=true, includeDetails=true)
# ADHD-ranked: priority desc → complexity asc (quick wins surface first)
```

### Energy matching + hyperfocus protection

The Python ADHD engine (see [adhd-patterns.md](adhd-patterns.md)) queries orchestrator candidates, then re-ranks by current energy + complexity. Read-only — never modifies orchestrator state. Sprint-level: cap simultaneous `work` items per operator at 1-2 to prevent attention fragmentation. Per-session: 25-min focus, 60-min warn, 90-min mandatory break (engine-enforced).

---

## Relationship System

Two link kinds, two systems. Use the right one.

### Intra-workflow dependencies → orchestrator `manage_dependencies`

Use for sprint-internal sequencing: subtask BLOCKS subtask, story BLOCKS story, etc.

```
manage_dependencies(operation="create", dependencies=[{
  itemId: "<dependent-uuid>",
  blockedBy: "<blocker-uuid>",
  unblockAt: "terminal"   # or "review"
}])
```

`get_blocked_items` surfaces dependent items; cascades fire automatically when the blocker reaches `unblockAt`.

### Cross-domain genealogy → ConPort linkage convention

ConPort `link_conport_items` only links ConPort entities (decision / system_pattern / progress_entry / custom_data). To record a **decision↔orchestrator work-item** edge, follow the convention in [orchestrator-note-filling-protocol.md](../../../docs/03-reference/orchestrator-note-filling-protocol.md):

1. Store the orchestrator work-item UUID in the ConPort decision's `implementation_details` (or tag with `orchestrator:<uuid>`).
2. Optionally create a ConPort `custom_data` shadow entry (`category: "orchestrator-shadow"`, `key: <uuid>`, `value: {title, role}`) and link via `link_conport_items` if you need bidirectional graph traversal.

For decisions↔ADRs and similar pure-ConPort genealogy, use the standard verbs: `builds_upon`, `validates`, `extends`, `implements`, `depends_on`, `supersedes`, `clarifies`, `resolves`, `tracks`.

---

## Cross-reference Map

- [authority-matrix.md](../coordination/authority-matrix.md) — system authority boundaries, violation prevention.
- [superclaude-workflows.md](superclaude-workflows.md) — `/sc:` vs `/dx:` integration patterns.
- [event-patterns.md](event-patterns.md) — workflow event payloads.
- [adhd-patterns.md](adhd-patterns.md) — ADHD engine, energy, sessions, breaks.
- [governance-principles.md](governance-principles.md) — Truth Order, PAL chain rules.
- [.claude/CLAUDE.md](../../CLAUDE.md) — Claude Code project floor + Orchestrator Operations.
- [AGENTS.md](../../../AGENTS.md) — Codex floor; §5 PAL chains, §9 proof bundle.
- [orchestrator-note-filling-protocol.md](../../../docs/03-reference/orchestrator-note-filling-protocol.md) — canonical note-filling loop.
- [.taskorchestrator/config.yaml](../../../.taskorchestrator/config.yaml) — `sprint-goal` + `retrospective` schemas.

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│            mem4sprint v2 Quick Reference                    │
├─────────────────────────────────────────────────────────────┤
│ Open sprint:     manage_items(type="sprint-goal", ...)      │
│                  + manage_notes(key="goal-definition")      │
│                  + advance_item(trigger="start")            │
│ Populate:        create_work_tree(parentId=<goal-uuid>)     │
│ Run:             /dx:next → work → proof-bundle → complete  │
│ Retrospective:   work-item with schema "retrospective"      │
│ Close:           confirm children terminal + retro terminal │
│                  + advance_item(trigger="complete")         │
│                  (no sprint-level proof-bundle; rolls up)   │
│ Abandon:         advance_item(trigger="cancel")             │
│                                                             │
│ Decisions:       conport/log_decision                       │
│ Risks/Metrics:   conport/log_custom_data                    │
│ Cross-domain:    conport/link_conport_items                 │
│ Workflow deps:   manage_dependencies (BLOCKS)               │
└─────────────────────────────────────────────────────────────┘
```

**Workflow state**: task-orchestrator owns it. ConPort retains decisions, knowledge graph, active_context, risks/metrics — see [authority-matrix.md](../coordination/authority-matrix.md) for the canonical split.

**See `~/.claude/MCP_ConPort.md`** for ConPort tool details; **`.taskorchestrator/config.yaml`** for current schemas.
