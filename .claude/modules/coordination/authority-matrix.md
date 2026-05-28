# Authority Matrix Module

**Module Version**: 2.0.0 (Simplified Architecture)
**Purpose**: Clear System Authority Boundaries Reference
**Usage**: Quick reference for preventing authority violations
**Decision Reference**: #132, #133, #134 (Simplified architecture)

## 🚨 CRITICAL AUTHORITY BOUNDARIES

### System Authority Matrix

| System | OWNS (Exclusive Authority) | NEVER Does |
|--------|---------------------------|------------|
| **task-orchestrator (MCP)** | **Workflow state machine** (queue→work→review→terminal+blocked)<br/>**Role transitions** (start, complete, block, resume, cancel, reopen, cascade)<br/>**Gate enforcement** (required notes per phase via schemas)<br/>**Complete-gate**: `proof-bundle` note required for `advance_item(complete)` per AGENTS.md §9<br/>**Dependencies** (BLOCKS edges with unblockAt thresholds)<br/>**Claim mechanism** (worktree-parallel coordination)<br/>**Schema config** (`.taskorchestrator/config.yaml` — contract-sensitive surface per AGENTS.md §6) | PM entity storage (Leantime owns)<br/>Decision rationale storage (ConPort owns)<br/>Code navigation<br/>ADHD recommendations<br/>Memory/chronicle (dope-memory owns) |
| **ConPort (PostgreSQL AGE)** | **Decisions** (`log_decision`, rationale, ADR linkage)<br/>**Decision genealogy** (`link_conport_items` — relates_to / implements / supersedes)<br/>**Knowledge graph** (architectural relationships, patterns)<br/>**Active/product context** (session resume, project metadata)<br/>**Structured progress receipts** (audit trail, not workflow state)<br/>**Semantic context recall** (`semantic_search_conport`) | **Workflow state** (task-orchestrator owns)<br/>**Role transitions** (task-orchestrator owns)<br/>PRD parsing<br/>ADHD metric calculation<br/>LSP operations |
| **SuperClaude** | PRD parsing via `/dx:prd-parse`<br/>25 standard commands execution<br/>15 specialized agents<br/>`/dx:` custom command routing — including orchestrator wrappers (`/dx:next`, `/dx:context`, `/dx:start`, `/dx:complete`, etc.)<br/>Human review workflow | Workflow state (task-orchestrator owns)<br/>Decision logging (ConPort owns)<br/>Code navigation<br/>ADHD state tracking |
| **Python ADHD Engine** | Energy tracking & matching<br/>Cognitive load calculation (0-1)<br/>Break monitoring (25/60/90min)<br/>Attention state analysis<br/>Smart task recommendation — **queries task-orchestrator for candidates**; does NOT modify workflow state<br/>Hyperfocus protection | Workflow state mutations<br/>PRD parsing<br/>LSP operations<br/>Knowledge graph management |
| **Serena LSP** | LSP protocol operations<br/>Code navigation & completion<br/>Symbol search & analysis<br/>Semantic code understanding<br/>Tree-sitter parsing<br/>Navigation caching | Task management<br/>Decision storage<br/>PRD decomposition<br/>Session timing |
| **React Ink Dashboard** | Visual workflow + task progress display<br/>ADHD metric visualization<br/>Real-time event rendering (subscribes to orchestrator events via bridge)<br/>User interaction surface (operator picks items)<br/>Break reminders & notifications | Task data storage<br/>Business logic<br/>Authority decisions<br/>Data persistence |
| **Integration Bridge** | Async event routing (Redis Streams)<br/>Event bus pub/sub coordination — including orchestrator event emission (item-started, item-completed, item-blocked, dependency-satisfied)<br/>MetaMCP role enforcement<br/>Multi-instance isolation | Task storage<br/>Workflow decisions<br/>PRD parsing<br/>ADHD calculations |
| **Leantime** | PM entity storage (projects, sprints, milestones, tickets as PM entities)<br/>Team-visible operational state | Workflow legality (task-orchestrator owns) — Leantime status alone does NOT establish workflow legality per the workflow-authority ADR |
| **dope-memory** | Temporal chronicle of work events<br/>Working-context per worktree instance | Workflow authority<br/>Decision authority |
| **dope-context** | AST-aware code+docs hybrid search<br/>Semantic retrieval over code/docs | Workflow / decision / chronicle authority |

## 🔄 Communication Flow Patterns

### Allowed Communication Paths (Simplified Architecture)

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│ SuperClaude │────>│ Python Validator │────>│   ConPort   │
│/dx:prd-parse│     │ (ADHD metadata)  │     │ (batch imp) │
└─────────────┘     └──────────────────┘     └─────────────┘
                                                     │
                                                     v
                                              ┌──────────────┐
                                              │ Integration  │
                                              │    Bridge    │
                                              │ (event pub)  │
                                              └──────────────┘
                                                     │
                          ┌──────────────────────────┼──────────────┐
                          v                          v              v
                   ┌─────────────┐          ┌────────────┐  ┌──────────┐
                   │   ADHD      │          │  Dashboard │  │  Serena  │
                   │   Engine    │          │  (React)   │  │   LSP    │
                   └─────────────┘          └────────────┘  └──────────┘
```

### Implementation Flow Example

```
1. User: /dx:next (or /dx:implement)
   └─> task-orchestrator.get_next_item(includeAncestors=true)
       └─> Returns ranked candidates with schema + gate status
           └─> ADHD Engine cross-checks energy fit
               └─> User picks item → /dx:start <id>
                   └─> advance_item(trigger="start", actor={...})
                       └─> Integration Bridge publishes "item-started"
                           ├─> Dashboard shows timer + breadcrumb
                           └─> ConPort.update_active_context({current_item: <id>})

2. During work
   └─> manage_notes(upsert, key="implementation-evidence", role="work")
       └─> File commits, validation exit codes accumulate
           └─> (No automatic ConPort write; ConPort gets a decision log if architectural)

3. At completion
   └─> /dx:complete <id>
       └─> manage_notes(upsert, key="proof-bundle", role="review")
           └─> Body: AGENTS.md §9 proof bundle
       └─> advance_item(trigger="complete")  ← FAILS without proof-bundle filled
           └─> Bridge publishes "item-completed"
               ├─> Dashboard celebrates
               └─> ConPort.log_decision(rationale, link_conport_items → orchestrator item)

4. At 25 minutes: Break reminder (orthogonal to workflow)
   └─> ADHD Engine triggers break
       └─> Integration Bridge publishes "break_reminder"
           └─> Dashboard shows notification: "Great work! Time for 5min break"
```

## ⚡ Event Flow Authority

### Task Lifecycle Events

| Event Type | Authoritative Source | Can Update | Can Read | Event Flow |
|------------|---------------------|------------|----------|-----------|
| **Workflow state** (role, gates, transitions) | task-orchestrator | task-orchestrator only via `advance_item` | All systems | orchestrator → Bridge ("item-started", "item-completed", "item-blocked") → All subscribers |
| **Work-item creation** | SuperClaude + Human (or any agent with MCP access) | Any agent via `manage_items(create)`; tag/type-based schema match auto-applies | All systems | agent → orchestrator → Bridge → All |
| **Note authoring** (PAL chain, proof-bundle, evidence) | The agent producing the artifact | Anyone via `manage_notes(upsert)` (with `actor` attribution) | All systems | agent → orchestrator → Bridge |
| **Decisions** (rationale, ADRs, genealogy) | ConPort | ConPort only via `log_decision` | All systems | ConPort → Bridge → All |
| **Decision↔work-item link** | ConPort + orchestrator | `link_conport_items` for ConPort side; `query_dependencies` for orchestrator side | All systems | manual cross-link convention per `docs/03-reference/orchestrator-note-filling-protocol.md` |
| **ADHD State** | Python ADHD Engine | ADHD Engine only | Dashboard, orchestrator (read-only for recommendation) | ADHD Engine → Bridge → Dashboard |
| **Code Navigation** | Serena LSP | Serena only | ADHD Engine (for context) | Serena → (optional) ConPort decision → Bridge |
| **Session State** | ConPort `active_context` | ADHD Engine + slash commands update | Dashboard, ConPort | ADHD Engine → ConPort `update_active_context` → Bridge → Dashboard |

## 🛡️ Violation Prevention

### Common Violations to Prevent

❌ **Any system modifying workflow state outside of task-orchestrator**
- **Why wrong**: workflow legality lives in the orchestrator's state machine. Direct DB pokes or competing stores create drift.
- **Correct**: all role transitions go through `advance_item`; all required notes via `manage_notes(upsert)`.

❌ **Storing task workflow state in ConPort `progress_entry`**
- **Why wrong**: ConPort is decisions + knowledge graph; workflow state is now task-orchestrator. Duplicating creates split-brain.
- **Correct**: orchestrator owns workflow state; ConPort retains decision genealogy via `link_conport_items` referencing orchestrator item IDs.

❌ **Bypassing the complete-gate via `cancel` or by skipping `proof-bundle`**
- **Why wrong**: `proof-bundle` is the mechanical complete-gate per AGENTS.md §9. Bypassing the gate creates uncertified "done" items.
- **Correct**: file the proof bundle in the `proof-bundle` note (review phase) → `advance_item(trigger="complete")` succeeds.

❌ **Serena modifying workflow state**
- **Why wrong**: Serena is for code navigation. Workflow belongs to the orchestrator.
- **Correct**: Serena reads context, never modifies work-items.

❌ **SuperClaude directly storing decisions**
- **Why wrong**: SuperClaude parses PRDs and wraps the orchestrator. ConPort stores decisions.
- **Correct**: SuperClaude generates JSON → Human approves → ConPort `log_decision` + orchestrator `create_work_tree` for the resulting work-items.

❌ **ADHD Engine mutating orchestrator state**
- **Why wrong**: ADHD Engine recommends; the orchestrator owns advancement.
- **Correct**: ADHD Engine queries orchestrator (`get_next_item`) → recommends to user → user picks → user invokes `advance_item`.

❌ **Dashboard modifying ConPort or orchestrator directly**
- **Why wrong**: Dashboard is view layer only.
- **Correct**: Dashboard triggers user action → Python service or slash command → orchestrator/ConPort → Bridge event → Dashboard re-render.

❌ **Integration Bridge storing data**
- **Why wrong**: Bridge is routing only, not storage.
- **Correct**: Bridge routes events; orchestrator / ConPort / Serena / ADHD Engine / dope-memory store data.

❌ **Editing `.taskorchestrator/config.yaml` without ADR**
- **Why wrong**: Schema config is a contract-sensitive surface per AGENTS.md §6. Schema changes propagate across all in-flight items.
- **Correct**: ADR linkage + operator authorization + `schemas_metadata.retro_id` for genealogy.

### Authority Enforcement Checks

```python
# Integration Bridge enforces these rules
def check_authority(operation: str, requester: str) -> bool:
    AUTHORITY_RULES = {
        "create_work_item":      ["any_agent_with_mcp"],          # via manage_items(create)
        "advance_role":          ["task_orchestrator"],            # via advance_item
        "upsert_note":           ["any_agent_with_mcp"],           # via manage_notes(upsert)
        "store_decision":        ["conport"],                      # via log_decision
        "link_decision_to_item": ["conport"],                      # via link_conport_items
        "parse_prd":             ["superclaude"],                  # /dx:prd-parse
        "calculate_adhd_metrics":["adhd_engine"],
        "lsp_operations":        ["serena"],
        "route_events":          ["integration_bridge"],
        "edit_schema_config":    ["operator_with_adr"],            # contract-sensitive per AGENTS.md §6
    }

    allowed_systems = AUTHORITY_RULES.get(operation, [])
    if requester not in allowed_systems:
        raise AuthorityViolationError(
            f"{requester} cannot perform {operation}. "
            f"Only {allowed_systems} have authority."
        )
    return True
```

## 🎯 Quick Decision Guide

**Need to pick the next work item?** → `mcp__task-orchestrator__get_next_item` (or `/dx:next`)
**Need to advance a work item?** → `mcp__task-orchestrator__advance_item` (or `/dx:start`, `/dx:complete`)
**Need to file PAL chain output / proof bundle / evidence?** → `mcp__task-orchestrator__manage_notes(upsert)` (or `/dx:note`)
**Need to create a new work item / sub-tree?** → `mcp__task-orchestrator__manage_items(create)` or `create_work_tree` (set `type` for schema activation)
**Need to declare a dependency?** → `mcp__task-orchestrator__manage_dependencies(create, type="BLOCKS")` (or `/dx:depends`)
**Need to parse a PRD?** → SuperClaude `/dx:prd-parse` → batch into orchestrator via `create_work_tree`
**Need to log a decision with rationale?** → `mcp__conport__log_decision` (and `link_conport_items` to the orchestrator work-item for genealogy)
**Need to calculate energy level?** → Python ADHD Engine
**Need code navigation?** → Serena LSP
**Need chronicle / temporal context?** → dope-memory
**Need code/docs semantic search?** → dope-context
**Need to route events?** → Integration Bridge
**Need to show UI?** → React Ink Dashboard

**Need to coordinate multiple systems?** → orchestrator emits event via Bridge → All subscribers react

## 📊 Authority Decision Tree

```
┌─ Need to interact with work items?
│
├─ Pick / advance / block / resume / complete / cancel / reopen?
│  └─> mcp__task-orchestrator__advance_item (or /dx:* wrapper)
│
├─ File PAL chain output / proof bundle / evidence / observations?
│  └─> mcp__task-orchestrator__manage_notes(upsert)
│
├─ Create new work items?
│  └─> mcp__task-orchestrator__manage_items(create) or create_work_tree
│      (set type="task-packet" — or matching schema key — for gate enforcement)
│
├─ Parse PRD into work items?
│  └─> SuperClaude /dx:prd-parse → Human review → mcp__task-orchestrator__create_work_tree
│
├─ Recommend which item to work on?
│  └─> Python ADHD Engine queries task-orchestrator.get_next_item → recommends → user picks → user advances
│
└─ Display work items in UI?
   └─> React Ink Dashboard subscribes to orchestrator events via Integration Bridge

┌─ Need to interact with code?
│
├─ Navigate/search code?
│  └─> Serena LSP (go-to-definition, find-references, etc.)
│
├─ Store architectural decision about code?
│  └─> ConPort log_decision (Serena NEVER stores decisions)
│
└─ Analyze code complexity for ADHD?
   └─> Serena provides code context → Python ADHD Engine calculates

┌─ Need to manage ADHD accommodations?
│
├─ Calculate energy/attention state?
│  └─> Python ADHD Engine (owns all ADHD calculations)
│
├─ Store ADHD metadata about tasks?
│  └─> ConPort custom_data category "task_metadata"
│
├─ Track session timing?
│  └─> Python ADHD Engine (25min timer) → ConPort (stores history)
│
└─ Show break reminders?
   └─> Python ADHD Engine triggers → Integration Bridge → Dashboard displays
```

## 🔐 MetaMCP Role-Based Boundaries

Integration Bridge enforces tool-level access per role:

| Role | Max Tools | Allowed Operations | Authority Enforcement |
|------|-----------|-------------------|---------------------|
| **QUICKFIX** | 8 tools | Basic code fixes, simple task updates | Limited ConPort + Serena access |
| **ACT** | 10 tools | Full implementation, code nav, progress tracking | Full Serena + ConPort progress |
| **PLAN** | 9 tools | Architecture, consensus, decision logging | Zen + ConPort decisions |
| **RESEARCH** | 10 tools | Deep research, analysis, investigation | Zen + Exa + GPT-Researcher |
| **ALL** | 60+ tools | Full access (use sparingly - cognitive overload) | All systems |

**ADHD Principle**: Limit tools per role to reduce cognitive load while maintaining necessary capabilities.

---

**Migration Notes:**

**What Changed from v2.0 (2026-05-27)**:
- ✅ **Restored**: task-orchestrator (now the canonical **workflow authority** per [adr-task-orchestrator-as-workflow-authority](../../../docs/90-adr/adr-task-orchestrator-as-workflow-authority.md) — accepted). Earlier "removed" status reflected a temporary architectural pivot that was reversed when the workflow-authority gap became evident. v3.8.0 image with schema config now active.
- ✅ **Restored**: Leantime as PM operational system of record (per AGENTS.md §6). Leantime owns PM entities; defers workflow legality to task-orchestrator.
- ✅ **Restored**: dope-memory + dope-context (chronicle memory + retrieval, respectively, per AGENTS.md §6).
- ✅ **Reframed**: ConPort is now decisions + knowledge graph + structured progress receipts — NOT workflow state. Workflow state lives in task-orchestrator. Decision↔work-item genealogy via `link_conport_items`.
- ✅ Kept: SuperClaude for PRD parsing with human review; now also wraps orchestrator MCP via `/dx:` slash commands.
- ✅ Kept: Python ADHD Engine for cognitive optimization (queries orchestrator instead of modifying ConPort progress_entry).
- ✅ Kept: Integration Bridge (event routing for orchestrator events + ADHD metrics).
- ✅ Kept: Serena LSP (code intelligence).

**What Changed from v1.0**:
- ❌ Removed: Two-Plane architecture (PM Plane vs Cognitive Plane) — replaced by typed authority boundaries per AGENTS.md §6.
- ❌ Removed: Task-Master-AI (PRD parsing) — folded into SuperClaude `/dx:prd-parse`.

---

**See Also:**
- `.claude/modules/coordination/integration-bridge.md` - Event routing details
- `.claude/modules/superclaude-integration.md` - SuperClaude configuration
- [`docs/03-reference/orchestrator-note-filling-protocol.md`](../../../docs/03-reference/orchestrator-note-filling-protocol.md) — Cross-agent orchestrator protocol (canonical reference)
- [`docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`](../../../docs/90-adr/adr-task-orchestrator-as-workflow-authority.md) — Workflow authority decision (accepted)
- [`docs/90-adr/adr-task-orchestrator-claude-surface-integration.md`](../../../docs/90-adr/adr-task-orchestrator-claude-surface-integration.md) — Claude-surface integration ADR (proposed)
- [`.taskorchestrator/config.yaml`](../../../.taskorchestrator/config.yaml) — Schema config (8 schemas + 5 traits + status_labels)
- [`AGENTS.md §6, §9, §12`](../../../AGENTS.md) — Architecture boundaries, proof and finality, Codex orchestrator operations
