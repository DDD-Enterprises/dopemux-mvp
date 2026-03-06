# Source Code Context

> **TL;DR**: Core `dopemux` package. Type hints required, Pydantic for data, FastAPI patterns. Check `mcp__serena-v2__analyze_complexity()` before deep dives.

**Inherits**: Root context (MCP tools, Do/Don't rules)

---

## Package Structure

```
src/dopemux/
├── __init__.py
├── cli.py              # CLI entry point — registers groups via cli.add_command()
├── commands/           # CLI command groups (one file per group)
│   ├── autoresponder_commands.py
│   ├── capture_group_commands.py  # also exports _workflow_request()
│   ├── code_commands.py
│   ├── decisions_commands.py
│   ├── dev_commands.py
│   ├── extract_commands.py
│   ├── extractor_commands.py      # exports _run_extractor_runner, _run_repscan_runner
│   ├── memory_commands.py
│   ├── profile_commands.py
│   ├── trigger_group_commands.py
│   ├── update_commands.py
│   ├── upgrades_commands.py
│   └── workflow_group_commands.py
├── event_bus.py        # Event-driven communication
├── mcp/                # MCP tooling
├── embeddings/         # Embedding utilities
├── tmux/               # Tmux controller
├── claude_tools/       # Claude-specific tooling
└── config/             # Configuration management
```

> **CLI convention**: command files use `@click.group()` (not `@cli.group()`).
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
# Run tests for src
pytest tests/dopemux/ -v

# Check coverage
pytest tests/ --cov=src/dopemux --cov-report=html
```

---

## Key Entry Points

- `dopemux.cli:main` - CLI application
- `dopemux.event_bus:EventBus` - Event publishing/subscribing
- `dopemux.tmux.controller:TmuxController` - Tmux operations