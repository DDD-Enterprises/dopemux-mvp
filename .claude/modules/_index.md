# CLAUDE.md Module Directory Index

**Structure Version**: 2.0.0 (Plane-Aligned Architecture)
**Created**: September 28, 2025

## Directory Organization

This module directory implements a **plane-aligned architecture** that respects the Two-Plane Architecture boundaries and authority matrix.

### Project Management Plane (`pm-plane/`)
Modules for project management and task coordination systems:
- `task-master.md` - PRD parsing and AI-driven task decomposition commands
- `task-orchestrator.md` - Dependency analysis with 37 specialized orchestration tools
- `leantime.md` - Status synchronization and team dashboard integration

### Cognitive Plane (`cognitive-plane/`)
Modules for developer support and code intelligence:
- `serena-lsp.md` - LSP operations with ADHD accommodations (max 10 results, 3-level depth)
- `conport-memory.md` - Graph operations for decision logging and context preservation

### Coordination (`coordination/`)
Modules for cross-plane communication and integration patterns:
- `integration-bridge.md` - Event routing patterns and cross-plane coordination (PORT_BASE+16)
- `authority-matrix.md` - Clear reference for system authority boundaries

### Shared (`shared/`)
Modules for cross-cutting concerns and common patterns:
- `sprint.md` - mem4sprint framework with entity templates and workflows
- `event-patterns.md` - Event schemas and async handling patterns
- `adhd-patterns.md` - ADHD accommodations and attention state management

## Loading Strategy

**PLAN Mode** (Strategic):
- Load: pm-plane/task-master.md + shared/sprint.md + cognitive-plane/conport-memory.md
- Token budget: ~4000 tokens

**ACT Mode** (Execution):
- Load: cognitive-plane/serena-lsp.md + cognitive-plane/conport-memory.md + python.md
- Token budget: ~2500 tokens

## Authority Enforcement

Each module respects the authority matrix:
- **Leantime**: Status updates only (never task decomposition)
- **Task-Master**: PRD parsing only (never status changes)
- **ConPort**: Decisions and patterns only (never task hierarchy)
- **Serena**: Code navigation only (never project management)

## Cross-Plane Communication

All cross-plane communication MUST route through the Integration Bridge. No direct tool calls between planes are permitted.

## ADHD Optimizations

- Progressive loading: Base + Mode-specific + Task-specific = 4.5K tokens (77% reduction)
- Max 3 modules loaded simultaneously to prevent cognitive overload
- Visual progress indicators integrated throughout
- Attention-aware model selection based on cognitive state