# Dopemux Development Platform

**Project**: Python-based ADHD-optimized development platform
**Architecture**: Simplified (ConPort + SuperClaude + Python ADHD Engine)
**Mode**: PLAN/ACT-aware with modular authority boundaries
**Workspace**: `/Users/hue/code/dopemux-mvp`

## 🧠 Core ADHD Principles

- **Context Preservation**: Auto-save every 30 seconds, maintain awareness across interruptions
- **Gentle Guidance**: Encouraging, supportive language with clear next steps
- **Progressive Disclosure**: Essential info first, details on request
- **Decision Reduction**: Maximum 3 options to reduce cognitive overwhelm
- **Task Chunking**: Break work into 25-minute segments with visual progress

## ⚡ Simplified Task & Cognitive Architecture

### Task Management (ConPort + SuperClaude + Python ADHD Engine)
**Authorities**: Task storage, PRD decomposition, ADHD optimization, progress tracking
- **ConPort (PostgreSQL AGE)**: Task storage via progress_entry, metadata in custom_data, dependencies via link_conport_items, knowledge graph queries for unblocked tasks, decision logging
- **SuperClaude**: PRD parsing via `/dx:prd-parse` with Zen planner, 25 standard commands, 15 specialized agents, `/dx:` custom commands for ADHD workflows
- **Python ADHD Engine**: Energy tracking, cognitive load calculation, break monitoring, attention state analysis, smart task routing, hyperfocus protection
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
WORKSPACE_ID="/Users/hue/code/dopemux-mvp"

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
- **PRD Decomposition**: SuperClaude `/dx:prd-parse` with Zen planner (human review required)
- **ADHD Optimization**: Python ADHD Engine queries ConPort, no direct task modification
- **Decisions**: Log in ConPort only (single source of truth)
- **Code Navigation**: Serena LSP only (LSP protocol + semantic analysis)
- **Knowledge Graph**: ConPort PostgreSQL AGE only (decisions, patterns, relationships)

## 🎯 SuperClaude Integration (v4.1.5)

**Status**: Fully integrated with Dopemux MCP stack (Decision #142-144)

**Available Tools**:
- **25 Slash Commands**: `/sc:implement`, `/sc:workflow`, `/sc:research`, `/sc:analyze`, etc.
- **7 Behavioral Modes**: Brainstorming, Deep Research, Task Management, Token Efficiency, Orchestration, Introspection, Business Panel
- **16 Specialized Agents**: Frontend, Backend, Security, QA, DevOps, Performance, Refactoring, etc.

**MCP Customization**:
- `sequential` → `zen` (multi-model reasoning: thinkdeep, planner, consensus, debug, codereview)
- `tavily` → `exa` + `gpt-researcher` (neural search + deep research)
- Kept: `magic` (UI generation), `playwright` (testing), `context7` (docs), `serena` (code), `morphllm` (transforms)

**Workflow Integration**:
See `.claude/modules/shared/superclaude-workflows.md` for complete integration patterns, command selection guide, and ADHD session workflows.

**MCP Documentation**:
All Dopemux MCPs documented in `~/.claude/MCP_*.md` (auto-imported):
- MCP_Zen.md - Multi-model reasoning suite (6 tools)
- MCP_ConPort.md - Knowledge graph & task management (9 capabilities)
- MCP_Serena.md - Code intelligence v2 (LSP + semantic analysis)
- MCP_Exa.md - Neural search for simple queries
- MCP_GPTResearcher.md - Deep multi-source research

## 📚 Detailed Information Locations

When you need comprehensive details, refer to:

**SuperClaude Workflows**: `.claude/modules/shared/superclaude-workflows.md` (integration patterns, command selection, ADHD sessions)
**Task Management**: `.claude/modules/superclaude-integration.md`, `.claude/modules/custom-commands.md`
**Cognitive Plane**: `.claude/modules/cognitive-plane/` (serena-lsp.md, conport-memory.md)
**ADHD Engine**: `.claude/modules/adhd-patterns.md` (sessions, energy tracking, break management)
**Shared Systems**: `.claude/modules/shared/` (sprint.md, event-patterns.md, superclaude-workflows.md)
**Filesystem Organization**: `docs/03-reference/filesystem-guide.md` (directory structure, file placement rules)

## 🎖️ Success Metrics

**Target Improvements**: 77% token reduction ✅ | 85% ADHD task completion | Sub-2s context switching | Zero authority violations

---

**MCP Status**: Fully operational with ConPort auto-initialization
**Python Standards**: Type hints, pytest, PEP 8 with Black formatting, src/ layout
**ADHD Support**: Progressive disclosure, gentle guidance, visual progress indicators active