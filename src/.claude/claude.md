# Source Code Context

> **TL;DR**: Core `dopemux` package. Type hints required, Pydantic v2 for data, FastAPI patterns. Use Serena (`mcp__serena__*`) for symbol navigation before deep dives.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Package Structure

```
src/dopemux/
├── __init__.py
├── cli.py              # CLI entry point — registers groups via cli.add_command()
├── commands/           # CLI command groups (one file per group)
│   ├── audit_commands.py
│   ├── autoresponder_commands.py
│   ├── capture_group_commands.py  # also exports _workflow_request()
│   ├── cockpit_commands.py
│   ├── dcp_commands.py
│   ├── decisions_commands.py
│   ├── dev_commands.py
│   ├── extract_commands.py
│   ├── extractor_commands.py      # exports _run_extractor_runner, _run_repscan_runner
│   ├── extractor_validation.py, extractor_validation_ui.py
│   ├── instances_commands.py
│   ├── kernel_commands.py
│   ├── mcp_commands.py
│   ├── memory_commands.py
│   ├── orchestrator_commands.py
│   ├── personas_commands.py
│   ├── profile_commands.py
│   ├── rte_shared.py
│   ├── system_data_commands.py
│   ├── trigger_group_commands.py
│   ├── update_commands.py
│   ├── upgrades_commands.py
│   ├── workflow_group_commands.py
│   └── worktrees_commands.py
├── event_bus.py        # Event-driven communication
├── mcp/                # MCP tooling
├── embeddings/         # Embedding utilities
├── tmux/               # Tmux controller
├── claude/             # Claude Code integration: native_hooks.py (hook dispatcher), configurator.py, instruction_manager.py (personas)
├── claude_tools/       # Claude-specific tooling
└── config/             # Configuration management
```

Other top-level packages in `src/`: `conport`, `core`, `integrations`, `utils`, `dopemux_github_specialist`, `dopemux_pr_merge_specialist`, `dopemux_pr_steward` (console scripts in `pyproject.toml [project.scripts]`).

> **CLI convention**: `cli.py` is ~6.5k lines; it registers `commands/*` groups and still hosts 27 legacy inline commands (26 `@cli.command` + 1 `@click.command`). Put new commands in `commands/`. Command files use `@click.group()` (not `@cli.group()`).
> Imports within `commands/` use `..module` (parent package) not `.module`.

---

## Code Standards

### Required
- **Type hints** on all public functions
- **Pydantic models** for all data structures
- **Docstrings** for public APIs
- **Complexity < 10** per function

### Preferred Patterns

```python
# Function signature
async def process_task(
    task_id: str,
    context: TaskContext,
    *,  # Force keyword args
    timeout: int = 30
) -> TaskResult:
    """Process task with ADHD-aware timeouts."""
    ...

# Error handling
try:
    result = await service.call(request)
except ServiceError as e:
    logger.error(f"Service failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

---

## ADHD-Friendly Patterns

- **Small functions** - Single responsibility, < 20 lines
- **Early returns** - Reduce nesting
- **Explicit errors** - Clear exception types
- **Progress logging** - `logger.info(f"📊 Step {n}/{total}")`

---

## Testing

```bash
# Run all tests (from repo root) — see tests/.claude/claude.md
make test

# Check coverage
.venv/bin/python -m pytest tests/ --cov=src/dopemux --cov-report=html
```

---

## Key Entry Points

- `dopemux.cli:main` - CLI application
- `dopemux.event_bus:EventBus` - Event publishing/subscribing
- `dopemux.tmux.controller:TmuxController` - Tmux operations