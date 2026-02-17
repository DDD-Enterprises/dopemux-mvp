# PHASE A2 — MCP + PROXY DEFINITIONS (REPO)
Model: Gemini Flash 3
Goal: Produce REPO_MCP_SERVER_DEFS.json + REPO_MCP_PROXY_SURFACE.json

Hard rules:
- Only extract from repo files (not home).
- Evidence required for each server/field.
- Do not infer how MCP works, only config surfaces.

Inputs:
- Partitions containing: mcp-proxy-config*, start-mcp-servers.sh, compose files, docs describing MCP, .claude/.dopemux configs.

Task:
1) REPO_MCP_SERVER_DEFS.json:
   Extract every MCP server definition/config block:
   - server_id (stable)
   - server_name (literal)
   - command/args (if present)
   - env_vars (names only + any literal default/value if present)
   - working_dir / roots / allowed_paths (if present)
   - enabled/disabled flags
   - source_path + anchor_excerpt per field

2) REPO_MCP_PROXY_SURFACE.json:
   Extract proxy wiring:
   - proxy_config_files (list)
   - routing_rules (if present)
   - allowlists/denylists (paths/tools)
   - auth surfaces (env var names only; redact values)
   - coupling points to LLM instructions (if instruction files reference MCP)
   - evidence everywhere

Output files:
- REPO_MCP_SERVER_DEFS.json
- REPO_MCP_PROXY_SURFACE.json
