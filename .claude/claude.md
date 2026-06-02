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
- **Confidence states**: `exploring / low / medium / high / certain`. `certain` requires direct evidence; final confidence for repo-changing work must be `VERIFIED` per [AGENTS.md §8](../AGENTS.md).
- **Validation buckets**: report **PASS / FAIL / NOT_RUN** — never collapse `NOT_RUN` into `PASS`.
- **Contract-sensitive surfaces** (schemas, migrations, event payloads, MCP manifests, hooks, proof bundles) require canonical-writer inspection before editing.
- **Security**: least privilege, fail-closed, never expose secrets, strict tool isolation in MCP/agent flows.

**Required final response shape**: Change Summary · Authority Used · Analysis Performed · Validation Performed (PASS/FAIL/NOT_RUN) · Remaining Uncertainty · Files Touched · Git State · Rollback Plan · Requested Next Step. For repo-changing work, also produce the proof bundle from [AGENTS.md §8](../AGENTS.md).

**Full doctrine**: [.claude/modules/shared/governance-principles.md](modules/shared/governance-principles.md).

## 🧠 Core ADHD Principles

- **Context Preservation**: Manual `dopemux save` and `/dx:save` support context capture; Stop hooks can perform best-effort saves when the ADHD Engine is running. A background 30-second save loop is planned/configured behavior, not observed Claude runtime support.
- **Gentle Guidance**: Encouraging, supportive language with clear next steps
- **Progressive Disclosure**: Essential info first, details on request
- **Decision Reduction**: Maximum 3 options to reduce cognitive overwhelm
- **Task Chunking**: Use operator-managed 25-minute checkpoints with visual progress; automatic timer enforcement is not observed runtime support.

## ⚡ Simplified Task & Cognitive Architecture

### Task Management (ConPort + SuperClaude + Python ADHD Engine)
**Authorities**: Task storage, PRD decomposition, ADHD optimization, progress tracking
- **ConPort (PostgreSQL AGE)**: Task storage via progress_entry, metadata in custom_data, dependencies via link_conport_items, knowledge graph queries for unblocked tasks, decision logging
- **SuperClaude**: PRD parsing via `/dx:prd-parse` with PAL planner, 25 standard commands, 15 specialized agents, `/dx:` custom commands for ADHD workflows
- **Python ADHD Engine**: Energy tracking, cognitive load calculation, break monitoring, attention state analysis, smart task routing, and hyperfocus-support modules. Claude-facing timer, break, and forced-pause automation remains not proven wired unless an explicit command/service path is verified.
- **React Ink Dashboard**: Visual task progress, ADHD metrics, attention-aware UI, real-time updates

### Cognitive Plane
**Authorities**: Code intelligence, navigation, context preservation, semantic understanding
- **Serena LSP**: Full LSP server with ADHD accommodations (max 10 results, 3-level context depth), semantic code analysis, navigation caching, Tree-sitter parsing, claude-context MCP integration
- **ConPort**: Decision logging, knowledge graph, architectural relationship tracking, pattern storage, session persistence

### Integration Layer
**Event-Driven Coordination**: Redis Streams + EventBus + Integration Bridge
- **Authority Enforcement**: Tool-level boundaries enforced via MetaMCP role-based filtering
- **Event Routing**: SuperClaude → Python ADHD Engine → ConPort → Dashboard (all async)
- **Conflict Resolution**: ConPort is source of truth for tasks, decisions, and ADHD state

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
```bash
# Set mode and create sprint structure
mcp__conport__update_active_context --workspace_id "$WORKSPACE_ID" --patch_content '{"mode": "PLAN", "sprint_id": "S-2025.09"}'
mcp__conport__log_custom_data --workspace_id "$WORKSPACE_ID" --category "sprint_goals" --key "S-2025.09-G1" --value '{"type": "sprint_goal", "content": "Goal description", "sprint_id": "S-2025.09", "status": "planned"}'
```

### Authority Routing
- **Task Storage**: ConPort progress_entry + custom_data only (no external orchestrators)
- **PRD Decomposition**: SuperClaude `/dx:prd-parse` with PAL planner (human review required)
- **ADHD Optimization**: Python ADHD Engine queries ConPort, no direct task modification
- **Decisions**: Log in ConPort only (single source of truth)
- **Code Navigation**: Serena LSP only (LSP protocol + semantic analysis)
- **Knowledge Graph**: ConPort PostgreSQL AGE only (decisions, patterns, relationships)

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

**Observed runtime support**: Settings dispatch all lifecycle events through `native_hooks.py`; hook scripts provide best-effort context save on Stop, energy warnings before complex tools, and progress/edit event signals.

**Planned/specification behavior**: focus-session timers, periodic save loops, automatic break prompts, and forced hyperfocus pauses are not proven wired in the observed Claude runtime.

Hooks run outside the model's turn. If you want to change hook behavior, edit the dispatcher or `.claude/hooks/` scripts; routine settings tweaks should go through the `update-config` skill rather than hand-editing `settings.json`. Hook output reaches the model as `<user-prompt-submit-hook>` blocks — treat as user input.

## 📚 Detailed Information Locations

When you need comprehensive details, refer to:

**Governance Principles**: `.claude/modules/shared/governance-principles.md` (Truth Order, PAL workflow rules, canonical writers, contract-sensitive surfaces, validation policy, required response structure)
**SuperClaude Workflows**: `.claude/modules/shared/superclaude-workflows.md` (integration patterns, command selection, ADHD sessions)
**Task Management**: `.claude/modules/superclaude-integration.md`, `.claude/modules/custom-commands.md`
**Cognitive Plane**: `.claude/modules/cognitive-plane/` (serena-lsp.md, conport-memory.md)
**ADHD Engine**: `.claude/modules/shared/adhd-patterns.md` (sessions, energy tracking, break management; separates observed support from planned automation)
**Shared Systems**: `.claude/modules/shared/` (sprint.md, event-patterns.md, superclaude-workflows.md)
**Filesystem Organization**: `docs/03-reference/filesystem-guide.md` (directory structure, file placement rules)
**Harness features** (Plan mode, advisor, /loop, ToolSearch, Skill): `~/.claude/MODES_AND_TOOLS.md`

## 🎖️ Success Metrics

**Target Improvements**: 77% token reduction ✅ | 85% ADHD task completion | Sub-2s context switching | Zero authority violations

---

**MCP Status**: Fully operational with ConPort auto-initialization
**Python Standards**: Type hints, pytest, PEP 8 with Black formatting, src/ layout
**ADHD Support**: Progressive disclosure, gentle guidance, visual progress indicators active
