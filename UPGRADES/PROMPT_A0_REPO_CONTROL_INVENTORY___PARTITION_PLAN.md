# PHASE A0 — REPO CONTROL PLANE INVENTORY + PARTITION PLAN
Model: Gemini Flash 3 (fast scan)
Goal: Produce REPO_INVENTORY.json + REPO_PARTITIONS.json

Hard rules:
- Do not summarize “what the system does”. Only inventory + partitions.
- Deterministic output ordering: sort paths lexicographically.
- Ignore: .git/, node_modules/, .venv/, .taskx_venv/, dist/, build/, __pycache__/
- Prefer control plane artifacts: instruction files, config, compose, hooks, routers, MCP definitions.

Inputs:
- Repo filesystem snapshot (files included in this chunk)

Task:
1) Build REPO_INVENTORY.json listing every included file with:
   - path, size_bytes (if given), ext, top_level_dir, is_probably_control_plane (bool)
   Control plane = any of:
   - instruction files: AGENTS.md, CLAUDE.md, claude.md, .claude/**, docs/llm/**, prompts/**, **/*instructions*
   - control config: .dopemux/**, dopemux.toml, dopemux.toml.*, *.yaml/*.yml/*.toml in config/
   - MCP/proxy: mcp*, litellm*, *router*, *provider*, *proxy*, compose*.yml, docker-compose*.yml
   - hooks: .githooks/**, scripts/** that run automatically, CI workflows

2) Produce REPO_PARTITIONS.json:
   Partition strategy must be token-safe and *path-based* (no semantic clustering).
   Output 10–40 partitions max, each with:
   - partition_id (A0_P01..)
   - include_globs (list)
   - exclude_globs (list)
   - rationale (1 sentence)
   - estimated_file_count (rough)
   - priority (P0/P1/P2)
   Requirements:
   - P0 partitions MUST include instruction/config surfaces:
     .claude/**, AGENTS.md/CLAUDE.md, .dopemux/**, config/**, compose*/docker-compose*, .githooks/**, .github/**,
     litellm.config*, mcp-proxy-config*, tmux-dopemux-orchestrator.yaml, dopemux.toml*
   - Create a dedicated partition for “LLM instruction surfaces” even if scattered.

Output files:
- REPO_INVENTORY.json
- REPO_PARTITIONS.json

Output schema:
REPO_INVENTORY.json = { "files":[ { "path": "...", "ext":".md", "size_bytes":1234, "top_level":"docs", "is_probably_control_plane":true } ], "generated_at":"..." }
REPO_PARTITIONS.json = { "partitions":[ { "partition_id":"A0_P01", "include_globs":[...], "exclude_globs":[...], "priority":"P0", "estimated_file_count":12, "rationale":"..." } ], "generated_at":"..." }
