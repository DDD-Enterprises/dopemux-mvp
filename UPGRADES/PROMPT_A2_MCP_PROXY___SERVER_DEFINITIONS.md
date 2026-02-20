Goal: REPO_MCP_SERVER_DEFS.json, REPO_MCP_PROXY_SURFACE.json

Prompt:
- Extract MCP server definitions from:
  - mcp-proxy-config*.{json,yaml}, compose/**, scripts that launch servers (start-mcp-servers.sh)
- For each server:
  - name, command, args, env vars, ports, volumes, health checks, dependencies.
  - Include string-literal server names and any "aliasing" behavior.
- JSON only, cite every extracted field by line_range.