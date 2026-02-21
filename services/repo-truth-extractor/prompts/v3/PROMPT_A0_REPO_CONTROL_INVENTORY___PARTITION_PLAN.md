MODE: Mechanical extractor, zero interpretation.
INPUT: repo working tree (top-level), include hidden dirs shown in ls -la (not .git contents).
OUTPUT:
- REPOCTRL_INVENTORY.json: list files (path, ext, size, mtime, sha256 if available), plus first 30 non-empty lines for text.
- REPOCTRL_PARTITIONS.json: partitions by type:
  - instructions/prompts (CLAUDE.md, AGENTS.md, .claude/**, docs/** instruction files)
  - mcp/proxy configs (mcp-proxy-config*, start-mcp-servers.sh, compose/**)
  - hooks (.githooks/**, scripts called by hooks)
  - routers/provider ladders (litellm.config*, any router yaml/toml/json)
  - compose/service graphs (compose.yml, docker-compose*.yml, compose/**)
  - CI/gates (.github/**, pre-commit, ruff/mypy/pytest configs)
  - taskx surfaces (.taskx/**, .taskx-pin, task packets in repo)
RULES: JSON only. Every item must include path + line_range (or null if binary).