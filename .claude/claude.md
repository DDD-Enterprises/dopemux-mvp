# Dopemux Development Platform

**Project**: Python-based ADHD-optimized development platform
**Architecture**: Simplified (ConPort + SuperClaude + Python ADHD Engine)
**Mode**: PLAN/ACT-aware with modular authority boundaries
**Workspace**: `<workspace_root>`

## 🎯 Governance Principles

**Doctrine**: truth over fluency, inspect before editing, minimal correct change, deterministic systems first, fail closed when evidence is missing. This module elaborates the same Truth Order / proof-and-finality regime that [AGENTS.md](../AGENTS.md) mandates for Codex — keep both files in sync.

**Default workflow**: `inspect → analyze → trace → plan → challenge → implement minimally → validate → precommit → summarize truthfully`.

**Non-negotiables**:
- **Authority order**: latest user instruction → [AGENTS.md](../AGENTS.md) / Task Packet → runtime code → schemas → tests → config → docs → assumptions. Runtime outranks docs. Mark unresolved authority as `UNKNOWN`.
- **PAL chains**: governed by [AGENTS.md §5](../AGENTS.md) — Codex minimum (`analyze → planner → codereview → precommit`) and risky/architecture variant. Do not restate the chain elsewhere.
- **Confidence states**: `exploring / low / medium / high / certain`. `certain` requires direct evidence; final confidence for repo-changing work must be `VERIFIED` per [AGENTS.md §9](../AGENTS.md).
- **Validation buckets**: report **PASS / FAIL / NOT_RUN** — never collapse `NOT_RUN` into `PASS`.
- **Contract-sensitive surfaces** (schemas, migrations, event payloads, MCP manifests, hooks, proof bundles) require canonical-writer inspection before editing.
- **Security**: least privilege, fail-closed, never expose secrets, strict tool isolation in MCP/agent flows.

**Required final response shape**: Change Summary · Authority Used · Analysis Performed · Validation Performed (PASS/FAIL/NOT_RUN) · Remaining Uncertainty · Files Touched · Git State · Rollback Plan · Requested Next Step. For repo-changing work, also produce the proof bundle from [AGENTS.md §9](../AGENTS.md) — and per [§12 Orchestrator Operations](../AGENTS.md), the bundle goes into the `proof-bundle` note on the work-item that completes via `advance_item(trigger="complete")`.

**Full doctrine**: [.claude/modules/shared/governance-principles.md](modules/shared/governance-principles.md).

## 🧠 Core ADHD Principles

- **Context Preservation**: Auto-save every 30 seconds, maintain awareness across interruptions
- **Gentle Guidance**: Encouraging, supportive language with clear next steps
- **Progressive Disclosure**: Essential info first, details on request
- **Decision Reduction**: Maximum 3 options to reduce cognitive overwhelm
- **Task Chunking**: Break work into 25-minute segments with visual progress

## ⚡ Task & Cognitive Architecture

### Workflow Authority (task-orchestrator)

**Per [`AGENTS.md §6`](../AGENTS.md) + [adr-task-orchestrator-as-workflow-authority](../docs/90-adr/adr-task-orchestrator-as-workflow-authority.md) (accepted)**: task-orchestrator is the canonical workflow authority. Work-item state, role transitions, gates, blockers, and next-action logic live here.

- **task-orchestrator (MCP)**: workflow state machine (queue → work → review → terminal + blocked), schema-aware note gates, complete-gate enforcement via `proof-bundle`, claim mechanism for worktree-parallel coordination. 14 MCP tools. Schema config at [`.taskorchestrator/config.yaml`](../.taskorchestrator/config.yaml).
- **ConPort (PostgreSQL AGE)**: decisions, structured progress receipts, knowledge graph, semantic context. **NOT** task storage anymore — workflow state belongs to the orchestrator. ConPort retains `log_decision`, `update_active_context`, `link_conport_items` for decision genealogy and ADR linkage.
- **SuperClaude**: command coordination via `/sc:` + `/dx:` slash commands. Wrapping orchestrator MCP for ADHD-shaped operator UX (`/dx:next`, `/dx:context`, `/dx:tree`, `/dx:blocked`, `/dx:search`). Phase 2-4 of DMX-ORCH-CLAUDE-SURFACE.
- **Python ADHD Engine**: energy tracking, cognitive load, break monitoring, attention state — feeds task-routing recommendations. Queries orchestrator for candidate work-items; does NOT modify orchestrator state.
- **React Ink Dashboard**: visual surface for orchestrator state + ADHD metrics — subscribes to orchestrator events via integration bridge.

### Cognitive Plane
**Authorities**: Code intelligence, navigation, context preservation, semantic understanding
- **Serena LSP**: Full LSP server with ADHD accommodations (max 10 results, 3-level context depth), semantic code analysis, navigation caching, Tree-sitter parsing, claude-context MCP integration
- **ConPort**: Decision logging, knowledge graph, architectural relationship tracking, pattern storage, session persistence

### Integration Layer
**Event-Driven Coordination**: Redis Streams + EventBus + Integration Bridge
- **Authority Enforcement**: Tool-level boundaries enforced via MetaMCP role-based filtering
- **Event Routing**: orchestrator transitions → ADHD Engine + Dashboard (async); SuperClaude commands wrap orchestrator MCP directly
- **Conflict Resolution**: task-orchestrator owns workflow state; ConPort owns decisions/knowledge graph; never duplicate workflow state across both

## 🎯 Mode-Aware Operation

**PLAN Mode**: Architecture, sprint planning, story breakdown
- Load PM plane modules + decision modules
- Focus on strategic thinking and synthesis
- Log decisions with rationale in ConPort

**ACT Mode**: Implementation, debugging, testing
- Load cognitive plane + execution modules
- Focus on concrete changes and linking artifacts
- Track progress and create deliverables

**Mode Detection**: Automatic based on activity type and user context

## 🚀 Integration Points

### ConPort Memory Management (AUTOMATIC)
```bash
# Workspace ID for ALL ConPort calls
WORKSPACE_ID="<workspace_root>"

# Mandatory session initialization
mcp__conport__get_active_context --workspace_id "$WORKSPACE_ID"
mcp__conport__get_recent_activity_summary --workspace_id "$WORKSPACE_ID" --hours_ago 24
```

### Sprint Management (mem4sprint)

Sprint goals are task-orchestrator work-items with schema `sprint-goal` (lifecycle PERMANENT). ConPort `active_context` retains PLAN/ACT mode tracking; it does **not** store workflow state.

```bash
# 1. Mode hint via ConPort (mode tracking only — not workflow state)
mcp__conport__update_active_context --workspace_id "$WORKSPACE_ID" \
  --patch_content '{"mode": "PLAN", "sprint_id": "S-2025.09"}'

# 2. Create sprint goal in task-orchestrator
mcp__task-orchestrator__manage_items --operation create \
  --items '[{"title": "Sprint S-2025.09: <goal>", "type": "sprint-goal", "tags": "sprint,S-2025.09", "priority": "high"}]'
# → returns <sprint-goal-uuid>

# 3. Fill required goal-definition note (gates the start transition)
mcp__task-orchestrator__manage_notes --operation upsert \
  --notes '[{"itemId": "<sprint-goal-uuid>", "key": "goal-definition", "role": "queue", "body": "Sprint S-2025.09. Goal: <statement>. Linked stories: ... Definition of done: ..."}]'

# 4. Open the sprint
mcp__task-orchestrator__advance_item \
  --transitions '[{"itemId": "<sprint-goal-uuid>", "trigger": "start"}]'
```

Full methodology, entity mapping, and PRD decomposition flow: [`.claude/modules/shared/sprint.md`](modules/shared/sprint.md).

### Authority Routing
- **Workflow state + transitions**: task-orchestrator (MCP) — owns work-item roles, gates, dependencies, claim mechanism. Per [`AGENTS.md §6`](../AGENTS.md) + the accepted workflow-authority ADR.
- **Decisions + knowledge graph**: ConPort — `log_decision`, `link_conport_items`, semantic recall. ConPort decisions can be linked to orchestrator work-items for genealogy.
- **PRD Decomposition**: SuperClaude `/dx:prd-parse` with PAL planner (human review required) — output flows into orchestrator as queue items.
- **ADHD Optimization**: Python ADHD Engine queries task-orchestrator for candidates; does NOT modify workflow state.
- **Code Navigation**: Serena LSP only (LSP protocol + semantic analysis).
- **PM operational records**: Leantime (per `AGENTS.md §6`) — PM SoR for projects/sprints/milestones as PM entities; defers workflow legality to task-orchestrator.
- **Chronicle / memory**: dope-memory — historical receipts + temporal context.
- **Code + docs retrieval**: dope-context — AST-aware semantic search.

## 🎯 Orchestrator Operations (Claude Code floor)

Task-orchestrator is the canonical workflow authority (per [`AGENTS.md §6`](../AGENTS.md) + [`§12 Orchestrator Operations`](../AGENTS.md) + [adr-task-orchestrator-as-workflow-authority](../docs/90-adr/adr-task-orchestrator-as-workflow-authority.md)). This section is the Claude Code-facing floor — read it once and you can drive the orchestrator without slash commands or plugin.

**Canonical protocol**: [`docs/03-reference/orchestrator-note-filling-protocol.md`](../docs/03-reference/orchestrator-note-filling-protocol.md). Codex, Claude Code, Copilot, custom-agent files, and personas all inherit from this single source of truth. Read it before invoking orchestrator MCP tools.

### Claude Code floor (what every session must know)

1. **14 orchestrator MCP tools** are available: `manage_items`, `query_items`, `manage_notes`, `query_notes`, `manage_dependencies`, `query_dependencies`, `advance_item`, `claim_item`, `get_next_status`, `get_next_item`, `get_blocked_items`, `complete_tree`, `create_work_tree`, `get_context`.

2. **Schema config lives at** [`.taskorchestrator/config.yaml`](../.taskorchestrator/config.yaml). 8 schemas: `task-packet` (default for repo-changing work), `feature-implementation`, `bug-fix`, `rfc-proposal`, `audit-pack`, `sprint-goal`, `retrospective`, `default` (fallback). Each schema enumerates its notes; selection is type-first then tag-fallback then default.

3. **PAL chain notes** (`AGENTS.md §5`): chain stages map to note keys of the same name (`analyze`, `planner`, `codereview`, `precommit`). Risky chain adds `thinkdeep`, `challenge-*`. Each note's schema entry carries a `skill:` pointer (e.g. `pal:analyze`) so hooks/agents can dispatch the right tool.

4. **The complete-gate is mechanical**: `advance_item(trigger="complete")` on a `type="task-packet"` (or any change-producing schema) FAILS without a `proof-bundle` note filled in review phase. Per [`AGENTS.md §9`](../AGENTS.md) — no proof means incomplete. Per [§12](../AGENTS.md), the proof bundle goes INTO the note.

5. **Set `type` at creation** for reliable schema activation. Tag-only items fall through to the `default` schema (proof-bundle gate only). Example: `manage_items(operation="create", items=[{title, type:"task-packet", tags:"..."}])`.

6. **Standard note-filling loop** (workflow-guide §5.6):
   ```
   get_context(itemId)              → read guidancePointer + skillPointer
   (invoke the named skill if any)  → produce note content
   manage_notes(upsert)             → file the note
   (repeat until canAdvance: true)
   advance_item(trigger="start"|"complete", actor={...})
   ```

### `/dx:` slash command wrappers (Claude Code-specific surface)

Phase 2 shipped (`/dx:next`, `/dx:context`); Phase 4 ships the rest (start/complete/note/block/resume/cancel/reopen/depends/preview/complete-tree/backlinks/notes/claim/release). Until they all ship, the bare-MCP path above is the fallback.

| Command | Wraps |
|---|---|
| `/dx:next` | `get_next_item(includeAncestors=true, limit=3)` — ADHD-ranked, with ConPort cross-check |
| `/dx:context [id]` | `get_context(itemId=...)` — three modes: item / session-resume / health-check |
| `/dx:tree`, `/dx:blocked`, `/dx:search` | Phase 2 (pending: TP-CS-036/037/039) |
| `/dx:start`, `/dx:complete`, `/dx:note`, `/dx:block`, `/dx:resume`, `/dx:cancel`, `/dx:reopen`, `/dx:depends` | Phase 4 write commands |
| `/dx:preview`, `/dx:complete-tree`, `/dx:backlinks`, `/dx:notes`, `/dx:claim`, `/dx:release` | Phase 4 supplementary wrappers |
| `/dx:implement` | Existing — being rewritten to use orchestrator (TP-CS-041) |
| `/dx:retro` | Phase 6 (manual retrospective trigger) |
| `/dx:packet` | Phase 5a (full TP lifecycle wrapper per `AGENTS.md §4`) |

### Authority caveats specific to Claude Code

- The MCP wrapper at `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh` is **external** to this repo. Snapshots committed to [`scripts/external-references/`](../scripts/external-references/) for traceability. Do not modify the external wrapper without explicit authorization — that's outside repo authority per `AGENTS.md §6`.
- **Multi-spawn safety**: the wrapper enforces one orchestrator container per workspace (`--name task-orchestrator-<workspace_id>`). Opening a second Claude Code session in this project disconnects the first session's MCP. Per [`scripts/external-references/README.md`](../scripts/external-references/README.md).
- **Schema config is contract-sensitive** (`AGENTS.md §6`): do not edit `.taskorchestrator/config.yaml` without ADR linkage + operator authorization. Schema versioning lives in the file's `schemas_metadata` block.
- **Claims are self-reported** (Stage 1 trust). `actor_authentication.enabled: false` in config. Use the Dopemux actor-ID convention: `{id: "worktree-<basename>-<branch>", kind: "subagent", parent: "<session-id>"}`.

### Discovery sequence for a fresh Claude Code session

```
1. get_context()                                    # health-check: active, blocked, stalled items
2. /dx:next  OR  get_next_item(limit=3, includeAncestors=true)
3. /dx:context <id>  OR  get_context(itemId=<chosen>)
4. (work the standard protocol above)
```

For deeper detail see the canonical protocol doc linked at the top of this section.

---

## 🎯 SuperClaude Integration (v4.1.5)

**Status**: Fully integrated with Dopemux MCP stack (see ConPort decisions #142–144)

**Available Tools**:
- **25 Slash Commands**: `/sc:implement`, `/sc:workflow`, `/sc:research`, `/sc:analyze`, etc.
- **7 Behavioral Modes**: Brainstorming, Deep Research, Task Management, Token Efficiency, Orchestration, Introspection, Business Panel
- **16 Specialized Agents**: Frontend, Backend, Security, QA, DevOps, Performance, Refactoring, etc.

**MCP Customization**:
- `sequential` → `pal` (multi-model reasoning: thinkdeep, planner, consensus, debug, codereview; formerly named `zen`)
- `tavily` → `exa` + `gpt-researcher` (neural search + deep research)
- Kept: `magic` (UI generation), `playwright` (testing), `context7` (docs), `serena` (code), `morphllm` (transforms)

**Workflow Integration**:
See `.claude/modules/shared/superclaude-workflows.md` for complete integration patterns, command selection guide, and ADHD session workflows.

**MCP Documentation**:
All Dopemux MCPs documented in `~/.claude/MCP_*.md` (auto-imported):
- MCP_PAL.md - Multi-model reasoning suite (6 tools; formerly MCP_Zen)
- MCP_ConPort.md - Knowledge graph & task management (9 capabilities)
- MCP_Serena.md - Code intelligence v2 (LSP + semantic analysis)
- MCP_Exa.md - Neural search for simple queries
- MCP_GPTResearcher.md - Deep multi-source research

## 🪝 Lifecycle Hooks

The project's `.claude/settings.json` registers 10 lifecycle hooks (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `Stop`, `SubagentStop`, `PreCompact`, `SessionEnd`), all dispatched through one entry point: `src/dopemux/claude/native_hooks.py`. Individual hook scripts live under `.claude/hooks/` (e.g., `check_energy.sh`, `log_progress.sh`, `save_context.sh`, `track_file_edit.sh`, `prompt_analyzer.py`, `session_lifecycle.py`).

Hooks run outside the model's turn — they're how the project automates auto-save, energy/break tracking, and ConPort context preservation. If you want to change hook behavior, edit the dispatcher or `.claude/hooks/` scripts; routine settings tweaks should go through the `update-config` skill rather than hand-editing `settings.json`. Hook output reaches the model as `<user-prompt-submit-hook>` blocks — treat as user input.

## 📚 Detailed Information Locations

When you need comprehensive details, refer to:

**Governance Principles**: `.claude/modules/shared/governance-principles.md` (Truth Order, PAL workflow rules, canonical writers, contract-sensitive surfaces, validation policy, required response structure)
**SuperClaude Workflows**: `.claude/modules/shared/superclaude-workflows.md` (integration patterns, command selection, ADHD sessions)
**Task Management**: `.claude/modules/superclaude-integration.md`, `.claude/modules/custom-commands.md`
**Cognitive Plane**: `.claude/modules/cognitive-plane/` (serena-lsp.md, conport-memory.md)
**ADHD Engine**: `.claude/modules/shared/adhd-patterns.md` (sessions, energy tracking, break management)
**Shared Systems**: `.claude/modules/shared/` (sprint.md, event-patterns.md, superclaude-workflows.md)
**Filesystem Organization**: `docs/03-reference/filesystem-guide.md` (directory structure, file placement rules)
**Harness features** (Plan mode, advisor, /loop, ToolSearch, Skill): `~/.claude/MODES_AND_TOOLS.md`

## 🎖️ Success Metrics

**Target Improvements**: 77% token reduction ✅ | 85% ADHD task completion | Sub-2s context switching | Zero authority violations

---

**MCP Status**: Fully operational with ConPort auto-initialization
**Python Standards**: Type hints, pytest, PEP 8 with Black formatting, src/ layout
**ADHD Support**: Progressive disclosure, gentle guidance, visual progress indicators active