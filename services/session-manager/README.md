# Dopemux Multi-AI Session Manager

ADHD-optimized terminal interface for orchestrating multiple AI CLI instances with tmux-based coordination.

## Features

- **Multi-AI Coordination**: Run Claude Code, Gemini CLI, and Grok simultaneously
- **Chat-Driven Control**: Natural language + slash commands to control AI instances
- **ADHD Optimizations**: Energy-aware layouts, auto-save every 30s, break reminders
- **Context Preservation**: Resume sessions with full context after interruptions
- **Adaptive Interface**: 2-4 panes based on current energy state

## Quick Start

```bash
# Install dependencies
pip install -e .

# Launch orchestrator
dopemux-session-manager start

# Or with specific energy level
dopemux-session-manager start --energy high
```

## Architecture

**Phase 1: Tmux TUI MVP** (Current)
- 4-pane tmux layout with adaptive behavior
- Chat orchestrator in pane 3
- 3 AI instances in panes 0-2
- Auto-save to ConPort every 30s

**Phase 2: API Layer** (Conditional)
- RESTful API for programmatic access
- Only if monitoring use cases emerge

**Phase 3: Web Dashboard** (Conditional)
- Visual monitoring and analytics
- Only if >60% users request it

## Development

```bash
# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Format code
black src/ tests/
ruff check src/ tests/ --fix
```

## Documentation

See `/Users/hue/code/ui-build/docs/` for:
- `DOPEMUX-ORCHESTRATOR-FINAL-SPEC.md` - Complete specification
- `DOPEMUX-MULTI-AI-ORCHESTRATOR-DESIGN.md` - Visual mockups
- `dopemux-session-manager-roadmap.md` - Implementation plan

## License

Part of Dopemux Two-Plane Architecture Orchestrator
