# Prompt B (v2): Interfaces (CLI + API + MCP + Hooks)

**Outputs:** `CLI_SURFACE.json`, `API_SURFACE.json`, `MCP_SURFACE.json`, `HOOKS_SURFACE.json`

---

## TASK

Produce FOUR JSON files: `CLI_SURFACE.json`, `API_SURFACE.json`, `MCP_SURFACE.json`, `HOOKS_SURFACE.json`.

## TARGET

`/Users/hue/code/dopemux-mvp` WORKING TREE.

## CLI_SURFACE.json

- Locate Typer/Click/argparse registrations.
- Emit items:
  - `domain=code_cli`
  - `kind=cli_command`
  - `name=<command name>`
  - `symbol=<handler function>`
  - `strings` must include flags/options and help text snippets.

## API_SURFACE.json

- Locate FastAPI route decorators (or other web frameworks).
- Emit items:
  - `domain=code_api`
  - `kind=api_route`
  - `name="<METHOD> <PATH>"`
  - `symbol=<handler function>`
  - `strings` include: `["method:GET", "path:/x", "dep:<depname>", "model:<ModelName>"]` if present.

## MCP_SURFACE.json

- Locate MCP tool registrations.
- Emit items:
  - `domain=code_mcp`
  - `kind=mcp_tool`
  - `name=<tool name>`
  - `symbol=<registration function if present>`
  - `strings` include schema keys (field names) and any defaults (top_k etc.) as strings.

## HOOKS_SURFACE.json

- Locate:
  - `.git/hooks` references
  - pre-commit hooks
  - internal "hooks" modules
  - workflow runner scripts invoked by hooks
- Emit items:
  - `domain=code_hook`
  - `kind=hook`
  - `name=<hook name or script>`
  - `symbol=<call target if present>`
  - `strings` include invoked commands.

## RULES

- No inference about behavior.
- Universal schema + deterministic sorting.
- If schema extraction is hard, include keys found as strings and set confidence=medium.
