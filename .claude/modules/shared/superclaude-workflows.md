# SuperClaude + Dopemux Workflow Integration

**Purpose**: Integration patterns for using SuperClaude commands with Dopemux's orchestrator-driven workflow stack.
**Audience**: Developers using Dopemux with SuperClaude framework.
**Module Version**: 2.0.0 (post-orchestrator-authority reconciliation, TP-CS-022)
**Authority Layer**: This file documents *how* surfaces fit together. Canonical authority for *what each system owns* lives in [authority-matrix.md](../coordination/authority-matrix.md).

> **What changed in 2.0**: workflow state moved from ConPort `progress_entry` to `task-orchestrator` (per [adr-task-orchestrator-as-workflow-authority](../../../docs/90-adr/adr-task-orchestrator-as-workflow-authority.md), accepted). "Zen" MCP was renamed to "PAL". This file is now a pointer-heavy integration guide, not a duplicate of canonical doctrine.

---

## Authority & Boundary Alignment

This file **IS** the operator-facing guide for `/sc:` (SuperClaude) and `/dx:` (Dopemux) command surfaces and how they hand off to the underlying MCP stack.

This file **IS NOT** the source of truth for:

| Topic | Canonical source |
|---|---|
| System authority boundaries | [authority-matrix.md](../coordination/authority-matrix.md) |
| Orchestrator MCP operations (note-filling, schemas, gates) | [.claude/CLAUDE.md §Orchestrator Operations](../../CLAUDE.md) + [orchestrator-note-filling-protocol.md](../../../docs/03-reference/orchestrator-note-filling-protocol.md) |
| Workflow event payload shapes | [event-patterns.md](event-patterns.md) |
| Per-MCP capability tables | `~/.claude/MCP_PAL.md`, `MCP_ConPort.md`, `MCP_Serena.md`, `MCP_Exa.md`, `MCP_GPTResearcher.md`, `MCP_DopeContext.md` (auto-imported via `~/.claude/CLAUDE.md`) |
| ADHD engine internals (energy, breaks, cognitive load) | [adhd-patterns.md](adhd-patterns.md) |
| PAL chain & proof-bundle complete-gate | [AGENTS.md §5 + §9](../../../AGENTS.md) |

If something here contradicts a canonical source, the canonical source wins.

---

## Command Selection Guide (`/sc:` vs `/dx:`)

Two command surfaces coexist:

- **`/sc:` (SuperClaude)** — 25 standard commands. Multi-agent coordination, framework workflows, broad task verbs. Lives at `~/.claude/commands/sc/`.
- **`/dx:` (Dopemux)** — orchestrator-wrapping commands plus Dopemux-specific UX. Lives at `~/.claude/commands/dx/` and `.claude/commands/dx/`.

### When to use which

| Situation | Prefer | Why |
|---|---|---|
| Picking next work item | `/dx:next` | ADHD-ranked, orchestrator-aware, includes ancestor breadcrumb. |
| Resuming after a break | `/dx:context` | Three modes: item / session-resume / health-check. |
| Standard implementation flow | `/sc:implement` | Coordinates Context7 + PAL + Magic + Playwright agents. (Note: `/dx:implement` is being rewritten to use orchestrator per TP-CS-041.) |
| Multi-step planning | `/sc:workflow` or `pal/planner` directly | Orchestrator stores result as work-items; `/sc:workflow` wraps `pal/planner`. |
| Deep research | `/sc:research` | Uses Exa + GPT-Researcher + PAL. |
| Bug investigation | `/sc:troubleshoot` (or `pal/debug` directly) | Systematic hypothesis-driven debugging. |
| Decision logging | ConPort `log_decision` (no slash command yet) | Canonical decision authority. |

### /sc: catalog

25 commands shipped under `~/.claude/commands/sc/`: `analyze`, `brainstorm`, `build`, `business-panel`, `cleanup`, `design`, `document`, `estimate`, `explain`, `git`, `help`, `implement`, `improve`, `index`, `load`, `reflect`, `research`, `save`, `select-tool`, `spawn`, `spec-panel`, `task`, `test`, `troubleshoot`, `workflow`.

### /dx: shipping status (per [DMX-ORCH-CLAUDE-SURFACE](../../../docs/90-adr/adr-task-orchestrator-claude-surface-integration.md))

| Phase | Command | Status | Wraps |
|---|---|---|---|
| 2 | `/dx:next` | shipped | `get_next_item(includeAncestors=true, limit=3)` |
| 2 | `/dx:context` | shipped | `get_context(itemId=...)` |
| 2 | `/dx:tree` | queue (TP-CS-036) | `query_items(overview)` |
| 2 | `/dx:blocked` | queue (TP-CS-037) | `get_blocked_items` |
| 2 | `/dx:search` | queue (TP-CS-039) | `query_items(search)` + `query_notes(search)` |
| 4 | `/dx:start`, `/dx:complete`, `/dx:note`, `/dx:block`, `/dx:resume`, `/dx:cancel`, `/dx:reopen`, `/dx:depends` | not shipped | write commands; orchestrator state transitions |
| 4 | `/dx:preview`, `/dx:complete-tree`, `/dx:backlinks`, `/dx:notes`, `/dx:claim`, `/dx:release` | not shipped | supplementary wrappers |
| existing | `/dx:implement` | rewriting (TP-CS-041) | being rewritten to drive orchestrator instead of legacy progress tracking |
| 5a | `/dx:packet` | not shipped | full TP lifecycle wrapper per AGENTS.md §4 |
| 6 | `/dx:retro` | not shipped | manual retrospective trigger |

Until Phase 4 write commands ship, the bare-MCP path documented in [.claude/CLAUDE.md §Orchestrator Operations](../../CLAUDE.md) is the fallback (`manage_items`, `advance_item`, `manage_notes`).

---

## Primary Development Flow

The workflow follows the orchestrator's `queue → work → review → terminal` state machine. ConPort retains decision/genealogy roles; SuperClaude wraps PAL reasoning; Serena handles code navigation.

### Discovery and start

```
1. /dx:context                              # health check: active/blocked/stalled
2. /dx:next                                 # ADHD-ranked candidates with ancestors
3. /dx:context <id>                         # item-mode context: notes, gate status
4. advance_item(trigger="start", actor=...) # /dx:start wraps this in Phase 4
   └─> orchestrator transitions queue → work
       └─> emits item-started event (see event-patterns.md)
           ├─> Dashboard shows timer + breadcrumb
           └─> ADHD engine begins focus tracking
```

### During work

```
- Implementation via /sc:implement, direct Edit, pal calls, etc.
- File evidence into the work-phase note (advisory but recommended):
    manage_notes(upsert, key="implementation-evidence", role="work")
- PAL chain notes if you used them: analyze/planner at queue;
  codereview/precommit will be filed at review phase.
- Architectural decisions → ConPort log_decision (linked back to work-item).
```

### Completion (the proof-bundle gate)

```
1. Run pal/codereview + pal/precommit (mandatory for repo-changing work
   per AGENTS.md §5).
2. Commit on the appropriate branch.
3. Open PR if applicable.
4. File the proof-bundle note (review role, key="proof-bundle"):
     - TP path/ID, worktree path, branch, slices completed
     - files changed, validations (PASS/FAIL/NOT_RUN)
     - codereview/precommit status, commit SHA, PR URL
     - residual risks, UNKNOWNs, cleanup status
   Per AGENTS.md §9: no proof bundle means incomplete.
5. advance_item(trigger="complete", actor=...)  # /dx:complete wraps this in Phase 4
   └─> orchestrator validates proof-bundle present, transitions → terminal
       └─> emits item-completed event
           ├─> Dashboard celebrates
           ├─> Cascade-eligible ancestors auto-advance
           └─> ConPort decision recommended (link_conport_items → work-item)
```

If `advance_item(complete)` fails, the mechanical complete-gate is doing its job — file the missing proof-bundle, then retry.

> **Command status callout**: `/dx:start`, `/dx:complete`, `/dx:note`, `/dx:block`, `/dx:resume`, `/dx:cancel`, `/dx:reopen`, `/dx:depends` are **Phase 4 — not shipped yet**. Use bare `advance_item` / `manage_notes` directly today. See the `/dx:` shipping status table above.

For full event payload shapes, see [event-patterns.md](event-patterns.md).
For the standard note-filling loop, see [orchestrator-note-filling-protocol.md](../../../docs/03-reference/orchestrator-note-filling-protocol.md).

---

## ADHD Session Workflow

The Python ADHD Engine and the orchestrator are decoupled: the engine queries orchestrator state for candidate items, then layers energy/cognitive-load filters on top. The orchestrator never reads ADHD state. See [adhd-patterns.md](adhd-patterns.md) for engine internals.

### 25-minute focus session

```
Session start (≈2 min)
├─ /dx:context                       # restore session state
├─ /dx:next                          # ADHD-ranked candidates, filtered by current energy
└─ Pick + advance_item(trigger=start) # /dx:start ships in Phase 4

Implementation (≈20 min)
├─ /sc:implement, direct edits, pal calls
├─ ConPort active_context auto-saves periodically (hook-driven)
├─ Optional: manage_notes(upsert key=implementation-evidence) for running log
└─ Focus maintenance: avoid /dx:next mid-session

Session end (≈3 min)
├─ Either: file proof-bundle + advance_item(trigger=complete)   # work done
├─ Or:     advance_item(trigger=block) or just pause             # work persists
└─ ConPort log_decision if architectural choice was made

Break (5 min, mandatory after 25)
```

### Hyperfocus protection

```
60 min  → engine warns: "60 min coding. Consider a break."
90 min  → engine mandates 15-min break, triggers auto-save hook.
```

Hyperfocus events are emitted to the integration bridge but do not modify orchestrator state.

### Context-switch recovery

```
Interrupted
├─ Auto-save hook → .dopemux/context.db updated
├─ Orchestrator work-item stays in work role
└─ ConPort active_context preserved

Resume
├─ /dx:context                  # session-resume mode: recent transitions + stalled
├─ Review work-phase notes      # what evidence was captured before interruption
└─ Continue, or advance_item(trigger=block) if stuck
```

### Energy-aware task selection

`/dx:next` already orders by orchestrator priority + complexity. For explicit energy matching, query `get_next_item(limit=10)` and let the engine re-rank against your current state (see [adhd-patterns.md](adhd-patterns.md) §energy matching).

---

## MCP Selection Quick Reference

When picking the right MCP for a sub-task. See per-MCP docs for capability detail.

| Task | Primary MCP | Reference |
|---|---|---|
| Multi-model reasoning (analyze/planner/codereview/debug/consensus) | PAL | [MCP_PAL.md](~/.claude/MCP_PAL.md) |
| Workflow state, gates, claims | task-orchestrator | [.claude/CLAUDE.md §Orchestrator Operations](../../CLAUDE.md) |
| Decisions, knowledge graph, active context | ConPort | [MCP_ConPort.md](~/.claude/MCP_ConPort.md) |
| Code navigation, LSP, semantic complexity | Serena | [MCP_Serena.md](~/.claude/MCP_Serena.md) |
| AST-aware code + docs search | dope-context | [MCP_DopeContext.md](~/.claude/MCP_DopeContext.md) |
| Simple web search | Exa | [MCP_Exa.md](~/.claude/MCP_Exa.md) |
| Deep multi-source research | GPT-Researcher | [MCP_GPTResearcher.md](~/.claude/MCP_GPTResearcher.md) |
| Framework docs | Context7 | per SuperClaude default |
| UI generation | Magic | per SuperClaude default |
| Browser/E2E testing | Playwright | per SuperClaude default |
| Bulk pattern transforms | Morphllm | per SuperClaude default |

### Authority routing reminder

Per [authority-matrix.md](../coordination/authority-matrix.md):

- Workflow state mutations → **task-orchestrator only** (never ConPort `progress_entry`).
- Decision authority → **ConPort only** (`log_decision`).
- Code navigation → **Serena only**.
- ADHD recommendations → **Python ADHD engine reads from orchestrator; never writes**.

---

## Cross-reference Map

- [authority-matrix.md](../coordination/authority-matrix.md) — system authority boundaries, violation prevention.
- [event-patterns.md](event-patterns.md) — workflow event payloads, routing rules.
- [adhd-patterns.md](adhd-patterns.md) — ADHD engine, energy, sessions, breaks.
- [governance-principles.md](governance-principles.md) — Truth Order, PAL chain rules, contract-sensitive surfaces.
- [sprint.md](sprint.md) — mem4sprint sprint scaffolding (ongoing reconciliation under TP-CS-023).
- [.claude/CLAUDE.md](../../CLAUDE.md) — Claude Code project floor + Orchestrator Operations.
- [AGENTS.md](../../../AGENTS.md) — Codex floor (§5 PAL chains, §6 authorities, §9 proof bundle, §12 Orchestrator Operations).
- [orchestrator-note-filling-protocol.md](../../../docs/03-reference/orchestrator-note-filling-protocol.md) — canonical note-filling loop.
- [adr-task-orchestrator-as-workflow-authority.md](../../../docs/90-adr/adr-task-orchestrator-as-workflow-authority.md) — accepted ADR establishing orchestrator as workflow SoR.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│            Dopemux + SuperClaude Quick Reference            │
├─────────────────────────────────────────────────────────────┤
│ Pick next work:        /dx:next                             │
│ Restore context:       /dx:context  (no args = health)      │
│ Start work-item:       advance_item(trigger="start")        │
│                        (/dx:start ships in Phase 4)         │
│ Complete work-item:    advance_item(trigger="complete")     │
│                        after proof-bundle  (/dx:complete    │
│                        ships in Phase 4)                    │
│ Standard implement:    /sc:implement <feature>              │
│ Deep research:         /sc:research <question>              │
│ Bug investigation:     /sc:troubleshoot <issue>             │
│ Decision logging:      conport/log_decision                 │
│ Note filing:           manage_notes(upsert, ...)            │
│                                                             │
│ Break reminder:        Every 25 min (engine)                │
│ Auto-save:             Every 5 min during work (hooks)      │
│ Hyperfocus warn:       60 min                               │
│ Mandatory break:       90 min                               │
└─────────────────────────────────────────────────────────────┘
```

**Workflow state**: task-orchestrator owns it. ConPort no longer stores task workflow state — see [authority-matrix.md](../coordination/authority-matrix.md) §Violation Prevention for why.

**PAL chain notes** (`analyze`/`planner`/`codereview`/`precommit`) and the `proof-bundle` complete-gate are mechanical orchestrator-side gates. See [AGENTS.md §5 + §9](../../../AGENTS.md) for the canonical chain definition.

---

**See `~/.claude/MCP_*.md`** for per-MCP details (auto-imported via `~/.claude/CLAUDE.md`).
**See `~/.claude/commands/sc/<command>.md`** for per-command details.
