Phase A goal
Extract the repo-resident control plane that modulates Dopemux behavior: instruction files, MCP configs, routers, hooks, compose/service wiring, env loaders, and workflow scripts.
Outputs are evidence indexes only, not truth.

Model
Gemini Flash 3 (Antigravity)
Hard rules
JSON only, ASCII only.
No “meaning”, no “purpose”, no “should”.
Every extracted item must include path and line_range (if line ranges are available).
Redact secrets deterministically.
A0: Control-plane inventory + partition plan
Outputs
REPO_CONTROL_INVENTORY.json
REPO_CONTROL_PARTITION_PLAN.json
ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.

TARGET ROOT: dopemux-mvp repo working tree.

ALLOWLIST PATHS (repo only):
- .claude/**
- .claude.json
- .claude.json.template
- AGENTS.md
- .dopemux/**
- .taskx/**
- .githooks/**
- compose.yml
- compose/**
- docker-compose*.yml
- docker/**
- start-mcp-servers.sh
- mcp-proxy-config*.json
- mcp-proxy-config*.yaml
- mcp-proxy-config*.yml
- litellm.config
- litellm.config.yaml
- litellm.config.yaml.backup
- dopemux.toml
- .env.example
- .env.smoke
- .envrc
- scripts/**
- tools/**
- tmux-dopemux-orchestrator.yaml
- dopemux.rb
- install.sh
- installers/**
- Makefile
- UPGRADE/**

OUTPUT 1: REPO_CONTROL_INVENTORY.json
For each file in allowlist paths:
- path
- size_bytes
- last_modified (if available)
- sha256 (if available)
- kind by extension only: json|yaml|toml|md|sh|rb|env|make|other
- is_probably_secret=true if filename contains any of: token, secret, key, password, credentials

OUTPUT 2: REPO_CONTROL_PARTITION_PLAN.json
Create deterministic partitions:
A1_INSTRUCTIONS = .claude/** + .claude.json* + AGENTS.md
A2_MCP_AND_PROXY = start-mcp-servers.sh + mcp-proxy-config* + compose.yml + compose/** + docker-compose*.yml
A3_ROUTING_AND_LITELLM = litellm.config* + .dopemux/** + any router configs found under config/ or scripts/
A4_HOOKS_AND_GITHOOKS = .githooks/** + any hook config files found in repo
A5_ENV_AND_BOOTSTRAP = .env.example + .env.smoke + .envrc + install.sh + installers/** + Makefile + dopemux.rb + tmux-dopemux-orchestrator.yaml
A6_TOOLS_SCRIPTS = scripts/** + tools/**

If any partition has > 30 files, split into subpartitions of 20 files each
named like A2_MCP_AND_PROXY__01, A2_MCP_AND_PROXY__02, etc.
Order files within partition by path ascending.

RULES:
- Do not read file contents in this step.
- JSON only.
- Deterministic ordering.
A1: Instruction plane surface (priority)
Outputs
REPO_INSTRUCTION_SURFACE.<partition_id>.json
REPO_INSTRUCTION_REFERENCES.<partition_id>.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- REPO_CONTROL_PARTITION_PLAN.json
PARAM: partition_id = <A1_INSTRUCTIONS or its subpartition>

SCOPE: files in that partition only.

TASK 1: REPO_INSTRUCTION_SURFACE.<partition_id>.json
For each instruction file (.md/.json/.yaml/.toml):
- path, line_range for key blocks when possible
- extract headings H1-H3 with line ranges (cap 120)
- extract any fenced code blocks ```...``` with:
  - language_hint
  - block_text capped to 120 lines
  - line_range

TASK 2: REPO_INSTRUCTION_REFERENCES.<partition_id>.json
Extract literal references to:
- MCP servers/tools (strings: "mcp", "mcp_servers", "server", "tool")
- commands and args (strings: "command", "args", "npx", "uvx", "docker", "compose")
- service names (strings matching compose services or "services/")
- file path references ("docs/", ".claude/", ".dopemux/", ".taskx/")

For each reference:
- ref_type = mcp|command|service|path|other
- excerpt <= 4 lines
- path, line_range

REDACTION:
- If excerpt contains tokens/keys/secrets/password/auth/bearer/cookie, replace value-like substrings with "REDACTED".

RULES:
- no inference
- JSON only
- deterministic ordering by path, then line_range
A2: MCP/proxy/compose surface (what actually runs)
Outputs
REPO_MCP_PROXY_SURFACE.<partition_id>.json
REPO_COMPOSE_SERVICE_GRAPH.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- REPO_CONTROL_PARTITION_PLAN.json
PARAM: partition_id = <A2_MCP_AND_PROXY or its subpartition>

SCOPE: files in that partition only.

TASK 1: REPO_MCP_PROXY_SURFACE.<partition_id>.json
Extract from mcp-proxy-config* and start-mcp-servers.sh and any proxy configs:
- server_name
- command
- args
- env var names referenced (values redacted)
- endpoints/ports if present (keep unless credential-like)
For each item include:
- path, line_range, excerpt <= 6 lines

TASK 2: REPO_COMPOSE_SERVICE_GRAPH.json
From compose.yml, docker-compose*.yml, compose/**:
Extract:
- services: name, build context or image, ports, env var names, volumes, depends_on
- networks and named volumes
Emit graph:
- nodes: services[]
- edges: depends_on relationships
- also list any scripts referenced (entrypoint/command)

REDACTION:
- redact values of env vars that look secret (token/key/password/secret/auth)
- keep env var names

RULES:
- JSON only
- no interpretation
- deterministic ordering
A3: Routing + LiteLLM + provider selection surface
Outputs
REPO_ROUTER_SURFACE.<partition_id>.json
REPO_LITELLM_SURFACE.<partition_id>.json
REPO_PROVIDER_LADDER_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- REPO_CONTROL_PARTITION_PLAN.json
PARAM: partition_id = <A3_ROUTING_AND_LITELLM or its subpartition>

SCOPE: files in that partition only.

TASK 1: REPO_LITELLM_SURFACE.<partition_id>.json
From litellm.config* and related YAML:
- model map keys
- router settings (fallbacks, retries, timeouts)
- database settings (db type, path or url keys) but redact credentials
- spend tracking toggles
Include excerpts <= 6 lines with path + line_range.

TASK 2: REPO_ROUTER_SURFACE.<partition_id>.json
Scan for literal patterns in allowlist files:
- "router", "routing", "fallback", "model", "provider", "tier", "policy"
Extract any blocks describing selection logic (config blocks, rule lists).
Include excerpt <= 6 lines with path + line_range.

TASK 3: REPO_PROVIDER_LADDER_HINTS.json
Extract any explicit ordered lists that look like fallback ladders:
- e.g. arrays/lists of providers/models
Emit as:
- ladder_id, items[], path, line_range

REDACTION:
- tokens/keys/secrets redacted

RULES:
- JSON only
- deterministic ordering
A4: Hooks + githooks + “implicit behavior” detection
Outputs
REPO_HOOKS_SURFACE.<partition_id>.json
REPO_IMPLICIT_BEHAVIOR_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- REPO_CONTROL_PARTITION_PLAN.json
PARAM: partition_id = <A4_HOOKS_AND_GITHOOKS or its subpartition>

SCOPE: files in that partition only.

TASK 1: REPO_HOOKS_SURFACE.<partition_id>.json
From .githooks/** and any hook configs:
- hook names (pre-commit, pre-push, etc.)
- scripts executed
- referenced tools/commands
- env vars referenced
Include excerpt <= 6 lines with path + line_range.

TASK 2: REPO_IMPLICIT_BEHAVIOR_HINTS.json
Extract references to:
- auto-start behaviors
- implicit server starts
- background daemons
- any "on save" / "hook" / "auto" / "implicit" keywords
Emit:
- hint_type, excerpt <= 4 lines, path, line_range

REDACTION:
- redact secret-like values

RULES:
- JSON only
- no inference
A5: Env + bootstrap + install surfaces (portability drivers)
Outputs
REPO_ENVVARS.json
REPO_BOOTSTRAP_SURFACE.<partition_id>.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- REPO_CONTROL_PARTITION_PLAN.json
PARAM: partition_id = <A5_ENV_AND_BOOTSTRAP or its subpartition>

SCOPE: files in that partition only.

TASK 1: REPO_ENVVARS.json
From .env.example, .env.smoke, .envrc, compose files in scope:
- extract env var NAMES only
- include source file path + line_range

TASK 2: REPO_BOOTSTRAP_SURFACE.<partition_id>.json
From install.sh, installers/**, Makefile, dopemux.rb, tmux-dopemux-orchestrator.yaml:
Extract:
- commands executed (lines invoking tools)
- referenced paths
- service names
Include excerpt <= 6 lines with path + line_range.

RULES:
- never output env var values
- JSON only
Phase A success signals
You are done with Phase A when you have:
REPO_CONTROL_INVENTORY.json
REPO_CONTROL_PARTITION_PLAN.json
all REPO_*_SURFACE.*.json artifacts for each partition chunk
REPO_COMPOSE_SERVICE_GRAPH.json
REPO_ENVVARS.json
No decisions. No synthesis.
