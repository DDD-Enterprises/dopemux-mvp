# Dopemux Two-Plane Architecture Orchestrator

**Project**: Multi-language ADHD-optimized development platform
**Languages**: Python (all versions), TypeScript, JavaScript, C, C++, Go, PHP
**Architecture**: Two-Plane with Integration Bridge coordination
**Mode**: PLAN/ACT-aware with modular authority boundaries
**Workspace**: `/Users/hue/code/dopemux-mvp`

## 🔧 Tool Usage Requirements

**CRITICAL: Always use Serena MCP tools for code operations**
- ✅ USE: `mcp__serena__read_file`, `mcp__serena__find_file`, `mcp__serena__list_dir`, `mcp__serena__find_symbol`
- ❌ NEVER: bash `cat`, `find`, `ls`, `grep` for code navigation
- **Why**: Serena provides LSP-aware semantic understanding, caching, and ADHD optimizations
- **Exception**: bash only for git, docker, system commands (not file operations)

## 🧠 Core ADHD Principles

- **Context Preservation**: Auto-save every 30 seconds, maintain awareness across interruptions
- **Gentle Guidance**: Encouraging, supportive language with clear next steps
- **Progressive Disclosure**: Essential info first, details on request
- **Decision Reduction**: Maximum 3 options to reduce cognitive overwhelm
- **Task Chunking**: Break work into 25-minute segments with visual progress

## ⚡ Two-Plane Architecture

### Project Management Plane
**Authorities**: Status updates, team visibility, task decomposition, dependencies
- **Leantime**: Status authority (planned→active→blocked→done), team dashboards
- **Task-Master**: PRD parsing, AI task decomposition, subtask hierarchies
- **Task-Orchestrator**: 37 specialized tools, dependency analysis, risk assessment

### Cognitive Plane
**Authorities**: Decisions, code navigation, memory, context preservation
- **Serena LSP**: Full LSP server with ADHD accommodations (max 10 results, 3-level context depth)
- **ConPort**: Decision logging, knowledge graph, automatic context preservation

### Coordination Layer
**Integration Bridge**: Cross-plane communication at PORT_BASE+16
- **Authority Enforcement**: No direct cross-plane communication allowed
- **Event Routing**: Task-Master → Integration Bridge → ConPort → Serena
- **Conflict Resolution**: Authoritative systems always win (Leantime for status, ConPort for decisions)

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
- **Status Updates**: Route to Leantime only
- **Task Decomposition**: Route to Task-Master only
- **Decisions**: Log in ConPort only
- **Code Navigation**: Use Serena LSP only
- **Cross-Plane**: Through Integration Bridge only

## 📚 Detailed Information Locations

When you need comprehensive details, refer to:

**PM Plane**: `.claude/modules/pm-plane/` (task-master.md, task-orchestrator.md, leantime.md)
**Cognitive Plane**: `.claude/modules/cognitive-plane/` (serena-lsp.md, conport-memory.md)
**Coordination**: `.claude/modules/coordination/` (integration-bridge.md, authority-matrix.md)
**Shared Systems**: `.claude/modules/shared/` (sprint.md, event-patterns.md, adhd-patterns.md)

## 🎖️ Success Metrics

**Target Improvements**: 77% token reduction ✅ | 85% ADHD task completion | Sub-2s context switching | Zero authority violations

---

**MCP Status**: Fully operational with ConPort auto-initialization
**Python Standards**: Type hints, pytest, PEP 8 with Black formatting, src/ layout
**ADHD Support**: Progressive disclosure, gentle guidance, visual progress indicators active