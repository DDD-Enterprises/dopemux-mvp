# PAL Stdio MCP Server

This variant runs PAL's core `server.py` directly on stdio for Docker MCP Toolkit integration.

## Usage

Build:
```bash
docker compose build pal-stdio
```

The container runs `server.py` which speaks MCP over stdio. Docker MCP Toolkit execs into it and exposes tools: thinkdeep, planner, consensus, debug, codereview, precommit, challenge, tracer, analyze.

## Differences from HTTP variant

- `pal` (HTTP): Runs `pal_http_wrapper.py` → exposes `/health`, `/sse`, `/mcp` on port 3003. Used by Claude Code via `~/.claude.json`.
- `pal-stdio` (this): Runs `server.py` directly on stdio. Used by Docker MCP Toolkit via `docker mcp server add`.

Both containers share the same source; only the entrypoint differs.
