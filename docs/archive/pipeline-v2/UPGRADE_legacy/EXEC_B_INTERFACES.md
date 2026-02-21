---
id: EXEC_B_INTERFACES
title: Exec B Interfaces
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Exec B Interfaces (explanation) for dopemux documentation and developer workflows.
---
# EXECUTABLE PROMPT: B - Interfaces (CLI + API + MCP + Hooks)

---

## YOUR ROLE

You are a **mechanical extractor**. Extract interface registrations by pattern-matching decorators, function signatures, and registration calls. No inference about runtime behavior.

---

## TASK

Scan the provided Python files and produce FOUR JSON files:
1. `CLI_SURFACE.json`
2. `API_SURFACE.json`
3. `MCP_SURFACE.json`
4. `HOOKS_SURFACE.json`

---

## OUTPUT 1: CLI_SURFACE.json

Find Typer/Click/argparse command registrations.

```json
{
  "path": "src/dopemux/cli.py",
  "line_range": [120, 145],
  "domain": "code_cli",
  "kind": "cli_command",
  "name": "start",
  "symbol": "start_command",
  "parent_group": "app",
  "decorator": "@app.command()",
  "params": [
    {"name": "--profile", "type": "str", "default": "default", "help": "Profile name"},
    {"name": "--altp", "type": "bool", "default": false, "help": "Use alt providers"}
  ],
  "help_text": "Start dopemux multiplexer session"
}
```

### Patterns to Match

- `@app.command()` / `@app.callback()` (Typer)
- `@click.command()` / `@click.group()` (Click)
- `parser.add_argument(...)` (argparse)

---

## OUTPUT 2: API_SURFACE.json

Find FastAPI/Flask/Starlette route decorators.

```json
{
  "path": "services/chronicle/main.py",
  "line_range": [55, 70],
  "domain": "code_api",
  "kind": "api_route",
  "name": "POST /events",
  "symbol": "create_event",
  "method": "POST",
  "route_path": "/events",
  "request_model": "EventCreate",
  "response_model": "EventResponse",
  "dependencies": ["get_db"],
  "tags": ["events"]
}
```

### Patterns to Match

- `@app.get("/...")` / `@app.post("/...")` / `@router.get("...")`
- `@app.route("/...", methods=[...])`
- Function params with type annotations (request models)

---

## OUTPUT 3: MCP_SURFACE.json

Find MCP tool/resource registrations.

```json
{
  "path": "services/dope-context/tools/search.py",
  "line_range": [10, 35],
  "domain": "code_mcp",
  "kind": "mcp_tool",
  "name": "search_context",
  "symbol": "search_context_tool",
  "schema_fields": ["query", "top_k", "filters"],
  "defaults": {"top_k": 10},
  "description": "Search the context store"
}
```

### Patterns to Match

- `@tool()` / `@server.tool()` decorators
- `Tool(name=..., ...)` instantiations
- `@server.resource()` for MCP resources

---

## OUTPUT 4: HOOKS_SURFACE.json

Find git hooks, pre-commit hooks, and internal hook modules.

```json
{
  "path": ".githooks/pre-commit",
  "line_range": [1, 15],
  "domain": "code_hook",
  "kind": "hook",
  "name": "pre-commit",
  "hook_type": "git_hook",
  "commands_invoked": ["python scripts/lint.py", "pytest tests/"],
  "excerpt": "#!/bin/bash\nset -e\npython scripts/lint.py"
}
```

### Patterns to Match

- Files under `.githooks/` or `.git/hooks/`
- `.pre-commit-config.yaml` entries
- Python modules named `*hook*` with registration patterns

---

## HARD RULES

1. **No inference** — extract literal text only
2. **JSON only** — no markdown, no prose
3. **ASCII only**
4. **Deterministic sorting** — by path, then line_range
5. **path + line_range required** on every item
6. **If a registration is ambiguous**, include it with `"confidence": "low"`

---

## OUTPUT FORMAT

Each file wrapper:

```json
{
  "artifact_type": "CLI_SURFACE",
  "generated_at_utc": "2026-02-15T22:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [...]
}
```

---

## BEGIN EXTRACTION

Process the provided context files and produce the four JSON outputs now.
