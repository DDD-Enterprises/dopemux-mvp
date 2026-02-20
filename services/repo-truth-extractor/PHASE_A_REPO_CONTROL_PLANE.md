# Phase A: Repo Control Plane (Flash/Grok)

## Phase A goal
Extract Repo Control Plane surfaces that modulate behavior:
Instruction files (Claude/Codex/agents) and how they reference tools/services
MCP proxy/server configs and server definitions
Router/provider ladders (model selection, fallbacks)
Hooks (git hooks, taskx hooks, any scripts run implicitly)
Compose graphs and environment wiring
LiteLLM configs (routing, logging, spend, DBs)
TaskX integration surfaces in repo (.taskx*, pins, operator profiles, templates)
Implicit behavior triggers (scripts invoked by Makefile, CI, installer, start scripts)
All outputs must be mechanical evidence indices.

## Preferred model
Primary: Grok-code-fast-1
Fallback: Gemini Flash 3

## Hard rules
JSON only, ASCII only.
Every item includes path + line_range + excerpt (<= N lines as specified).
Do not infer intent. Do not label semantics. Do not decide “authoritative”.
Stable ordering.

## A0: Repo control inventory + partition plan (mandatory)
Outputs
REPO_CONTROL_INVENTORY.json
REPO_CONTROL_PARTITION_PLAN.json
ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.
TARGET ROOT: dopemux-mvp repo working tree.

INCLUDE PATHS:
- .claude/**, .claude.json, .claude.json.template
- .dopemux/**, dopemux.toml, dopemux.rb
- .githooks/**, .git/hooks/** (if tracked), scripts/**, tools/**
- compose/**, compose.yml, docker-compose*.yml, docker/**, Dockerfile*
- AGENTS.md, CLAUDE.md, claude.md, README.md, QUICK_START.md, INSTALL.md
- litellm.config*, mcp-proxy-config*.y*ml/json, start-mcp-servers.sh
- .taskx/**, .taskx-pin, .taskxroot, .taskx_venv (just names)
- config/**, profiles/**, installers/**, install.sh, Makefile
- .github/** (workflow files)
- tmux-dopemux-orchestrator.yaml, .tmux.conf

OUTPUT 1: REPO_CONTROL_INVENTORY.json
For each included file:
- path
- size_bytes
- last_modified (if available)
- sha256 (if available)
- file_kind by extension (md|json|yaml|toml|sh|py|rb|other)
- first_nonempty_line (scan first 80 lines)
- contains_tokens[]: list of matched tokens from:
  ["mcp","litellm","router","provider","model","taskx","hook","compose","docker","tmux","agent","instruction","server","proxy","env","dotenv"]

OUTPUT 2: REPO_CONTROL_PARTITION_PLAN.json
Create deterministic partitions with explicit path lists:
A1_INSTRUCTIONS
A2_MCP_PROXY_AND_SERVERS
A3_ROUTER_PROVIDER_LADDERS
A4_HOOKS_AND_IMPLICIT_TRIGGERS
A5_COMPOSE_AND_SERVICE_GRAPH
A6_LITELLM_CONFIG_AND_LOGGING
A7_TASKX_REPO_SURFACE
A8_CI_AND_GATES

RULES:
- Partitioning is by path heuristics only.
- No interpretation.
- JSON only.

## A1: Instruction surfaces (priority treatment)
Outputs
REPO_INSTRUCTION_SURFACE.json
REPO_INSTRUCTION_REFERENCES.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE: Files likely to contain LLM instructions:
- .claude/**, AGENTS.md, CLAUDE.md, claude.md
- docs/**/custom-instructions/** (if present)
- docs/**/prompts*/** (if present)
- any file with "instruction" or "agent" in name from REPO_CONTROL_INVENTORY

TASK 1: REPO_INSTRUCTION_SURFACE.json
For each instruction-like block:
- path, line_range
- block_kind: markdown_section | yaml_block | json_block | plain_text
- excerpt <= 25 lines
- detected_directives[]: extract literal occurrences of:
  ["MUST","MUST NOT","NEVER","ALWAYS","STOP","Authority","Hierarchy","Invariants","No invention","Deterministic"]
- tool_mentions[]: literal tool/server names mentioned (e.g., "mcp", "filesystem", "memory", "conport", "serena", "dope-context", "taskx")

TASK 2: REPO_INSTRUCTION_REFERENCES.json
Extract explicit references to:
- file paths
- commands (lines starting with $, `make`, `docker`, `uv`, `python`, `node`, `taskx`)
- server configs (mcp, litellm, proxy)
For each reference:
- ref_kind: path|command|server|env|url
- value: literal string
- path, line_range, excerpt <= 6 lines

RULES:
- Do not interpret directives.
- JSON only.

## A2: MCP proxy + server definitions (repo)
Outputs
REPO_MCP_PROXY_SURFACE.json
REPO_MCP_SERVER_DEFS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- mcp-proxy-config*.yaml/json
- start-mcp-servers.sh
- docs/archive/mcp-servers/** (index only, do not infer)
- any compose files referencing mcp
- config files mentioning mcp in REPO_CONTROL_INVENTORY

TASK 1: REPO_MCP_PROXY_SURFACE.json
Extract:
- proxy config sections (servers, routes, env, auth, allowlists)
- path, line_range, excerpt <= 40 lines per section
Also emit:
- server_ids: literal keys/names if parseable

TASK 2: REPO_MCP_SERVER_DEFS.json
Extract server launch definitions:
- command + args
- env vars set for each server
- working dirs if specified
For each server:
- server_name
- command
- args[]
- env_kv[] (key only; redact values if sensitive)
- path, line_range, excerpt <= 20 lines

RULES:
- Redact secrets: if a value looks like key/token, output "***REDACTED***"
- JSON only.

## A3: Router + provider ladders (repo)
Outputs
REPO_ROUTER_SURFACE.json
REPO_PROVIDER_LADDER_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- .claude.json, .claude/**, .dopemux/**, dopemux.toml
- any "router" configs, "provider" configs, "model" lists
- litellm.config* (also covered in A6 but extract routing bits here too)

TASK 1: REPO_ROUTER_SURFACE.json
Extract any configuration that appears to route requests:
- provider selection rules
- trust levels
- project allowlists
- model settings (name, reasoning effort)
For each block:
- path, line_range, excerpt <= 40 lines
- detected_keys[] (keys only)

TASK 2: REPO_PROVIDER_LADDER_HINTS.json
Extract literal ordered lists of providers/models/fallbacks:
- arrays or bullet lists of providers/models
- environment variables controlling provider
For each ladder:
- ladder_id
- ordered_items[] (literal strings)
- path, line_range, excerpt <= 20 lines

RULES:
- No claims about which is used at runtime.
- JSON only.

## A4: Hooks + implicit triggers (repo)
Outputs
REPO_HOOKS_SURFACE.json
REPO_IMPLICIT_BEHAVIOR_HINTS.json
REPO_BOOTSTRAP_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- .githooks/**
- install.sh, installers/**, scripts/**, tools/**
- Makefile targets that call scripts
- .envrc, .env*, dopemux.rb (if it runs stuff)
- any "bootstrap", "start", "verify", "setup" scripts

TASK 1: REPO_HOOKS_SURFACE.json
Extract:
- hook files (pre-commit, post-checkout, post-merge, etc.)
- commands executed
For each hook:
- hook_name (filename)
- path, line_range, excerpt <= 40 lines

TASK 2: REPO_IMPLICIT_BEHAVIOR_HINTS.json
Extract command chains that can run implicitly:
- Makefile recipes
- installer scripts
- dev scripts that call other scripts
For each chain:
- chain_id
- steps[] (literal command lines)
- path, line_range, excerpt <= 30 lines

TASK 3: REPO_BOOTSTRAP_SURFACE.json
Extract "how the system starts":
- start scripts, compose up invocations, tmux layouts
For each:
- bootstrap_kind = compose|tmux|shell|python|node|other
- path, line_range, excerpt <= 40 lines

RULES:
- JSON only.
- No inference of purpose.

## A5: Compose + service graph (repo)
Outputs
REPO_COMPOSE_SERVICE_GRAPH.json
REPO_ENV_WIRING.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- compose.yml
- docker-compose*.yml
- compose/**

TASK 1: REPO_COMPOSE_SERVICE_GRAPH.json
Parse compose files and emit:
- services[]:
  - name
  - image/build (literal)
  - depends_on
  - ports
  - volumes
  - environment_keys[] (keys only; redact values)
  - command/entrypoint (literal)
  - networks
  - profiles
- file_sources[]: list of compose files used

TASK 2: REPO_ENV_WIRING.json
Extract:
- env files referenced
- environment variables used in compose as ${VAR}
Emit:
- var_name
- path, line_range, excerpt <= 6 lines
- used_in_service if parseable

RULES:
- JSON only.
- Redact suspicious values.

## A6: LiteLLM config + logging + spend DB surfaces (repo)
Outputs
REPO_LITELLM_SURFACE.json
REPO_LITELLM_DB_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- litellm.config
- litellm.config.yaml
- any file referencing "litellm"
- compose env for litellm
- docs about litellm (index only)

TASK 1: REPO_LITELLM_SURFACE.json
Extract:
- model definitions
- routers
- logging settings
- callbacks
- rate limits
- proxy settings
For each config block:
- path, line_range, excerpt <= 60 lines
- detected_keys[] (keys only)

TASK 2: REPO_LITELLM_DB_HINTS.json
Extract literal DB references:
- sqlite/postgres URLs
- file paths
- env vars for DB
For each:
- db_kind = sqlite|postgres|other|unknown
- path, line_range, excerpt <= 8 lines
- redacted_value if sensitive

RULES:
- JSON only.
- Redact values that look like credentials.

## A7: TaskX surfaces in repo (pinning, operator instructions, templates)
Outputs
REPO_TASKX_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- .taskx/**
- .taskx-pin
- .taskxroot
- docs/task-packets/**
- any scripts invoking taskx

Extract:
- pin versions and roots
- operator profile files and compiled prompt outputs if present
- task packet templates and locations
- any CLI invocations of taskx in scripts/make/ci

For each item:
- item_kind = pin|root|profile|template|packet|invocation|output
- path, line_range, excerpt <= 40 lines
- detected_fields[] (keys only) if yaml/json

RULES:
- JSON only.

## A8: CI + gates (repo)
Outputs
REPO_CI_GATES_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- .github/workflows/**
- .pre-commit-config.yaml
- pytest.ini, ruff/mypy configs
- scripts that look like CI gates

Extract:
- job steps that run tests/lint/format
- any artifact upload paths
- any environment requirements

For each gate:
- gate_kind = github_actions|precommit|pytest|ruff|mypy|other
- path, line_range, excerpt <= 60 lines
- commands[] (literal)

RULES:
- JSON only.

## A9: Merge + normalize + QA
Outputs
All normalized REPO_*.json in A_repo_control_plane/norm/
A_COVERAGE_REPORT.json
ROLE: Mechanical normalizer. No reasoning. JSON only. ASCII only.

INPUTS:
- all raw outputs from A0..A8

MERGE RULES:
- dedupe by (path, line_range, sha256(excerpt))
- stable sort by path then start line
- ensure each output has:
  - artifact_type
  - generated_at_local
  - inputs[] (file list)
  - items[]

QA OUTPUT: A_COVERAGE_REPORT.json
Include:
- expected_artifacts list
- present_artifacts list
- missing_artifacts list
- item_counts per artifact
- top_paths_by_items (top 25)
- redaction_count

JSON only.
