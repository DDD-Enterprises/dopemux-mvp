# CLAUDE.md Module Directory Index

**Structure Version**: 2.0.0 (Plane-Aligned Architecture)
**Created**: September 28, 2025

## Directory Organization

This module directory implements a **simplified architecture** with SuperClaude integration.

**Architecture Version**: 2.0 (Simplified with SuperClaude)
**Decision Reference**: #132, #133, #134 (Simplified), #142-144 (SuperClaude Integration)

### SuperClaude Integration
- `superclaude-integration.md` - SuperClaude 4.1.5 integration with Dopemux MCPs (COMPLETE)
- `custom-commands.md` - /dx: custom command specifications (planned)

### Cognitive Plane (`cognitive-plane/`)
Modules for code intelligence and knowledge management:
- `serena-lsp.md` - Serena v2 LSP with ADHD accommodations (max 10 results, 3-level depth, complexity scoring)
- `conport-memory.md` - ConPort PostgreSQL AGE for decisions, progress, knowledge graph

### PM Plane (`pm-plane/`) - Archived
**Note**: Per Decision #132-134, simplified to ConPort + SuperClaude. The three legacy module docs are retained for historical reference only — moved to `pm-plane/_deprecated/` as of 2026-05. Use ConPort `progress_entry` and the `link_conport_items` knowledge graph for all task management.

### Coordination (`coordination/`)
Modules for integration patterns and authority boundaries:
- `integration-bridge.md` - Event routing and system coordination
- `authority-matrix.md` - Authority boundaries (updated for simplified architecture)

### Shared (`shared/`)
Cross-cutting concerns and common patterns:
- `sprint.md` - Sprint management with ConPort integration
- `event-patterns.md` - Event-driven architecture patterns
- `adhd-patterns.md` - ADHD accommodations and SuperClaude session workflows
- `superclaude-workflows.md` - ConPort + Serena + SuperClaude integration patterns (NEW)

## Loading Strategy (Simplified Architecture)

**Session Start** (Always load):
- `shared/superclaude-workflows.md` - Primary workflow integration
- `cognitive-plane/conport-memory.md` - Knowledge graph and decisions
- Reference MCP docs via @ imports (conditional loading)

**PLAN Mode** (Strategic):
- `shared/sprint.md` - Sprint planning
- `cognitive-plane/conport-memory.md` - Decision logging
- Zen MCP for consensus and planning

**ACT Mode** (Implementation):
- `cognitive-plane/serena-lsp.md` - Code navigation
- `cognitive-plane/conport-memory.md` - Progress tracking
- SuperClaude commands (/sc:implement, /sc:fix, etc.)

**RESEARCH Mode**:
- Exa + GPT-Researcher for investigation
- Zen thinkdeep for analysis
- ConPort for logging findings

## Authority Enforcement (Simplified)

**Simplified Architecture Authorities** (Decision #132-134):
- **ConPort**: Task storage, decision logging, progress tracking, knowledge graph (PRIMARY)
- **SuperClaude**: Command coordination, PRD parsing (/sc:workflow + Zen planner), agent orchestration
- **Serena**: Code navigation, LSP operations, semantic analysis
- **Zen**: Multi-model reasoning, planning, debugging, code review
- **Python ADHD Engine**: Energy tracking, break monitoring, task routing (queries ConPort)
- **Leantime**: ⚠️ DEPRECATED - Use ConPort `progress_entry` for task status tracking

## ADHD Optimizations

- Progressive loading: Base + Mode-specific + Task-specific = 4.5K tokens (77% reduction)
- Max 3 modules loaded simultaneously to prevent cognitive overload
- Visual progress indicators integrated throughout
- Attention-aware model selection based on cognitive state