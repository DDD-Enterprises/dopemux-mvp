# Phase H: Home Control Plane (Flash/Grok)

## Phase H goal
Extract user-home control plane surfaces that modulate Dopemux/TaskX/LLM routing:
~/.dopemux/** (routers, sessions, profiles, local DBs, instance caches, mcp config)
~/.config/dopemux/** (config.yaml, dopemux.toml, dashboard.json, profiles)
~/.config/taskx/**
~/.config/litellm/**
~/.config/mcp/**
We do not ingest secrets. We extract keys, structure, and references.

## Outputs (normalized)
HOME_CONTROL_INVENTORY.json
HOME_CONTROL_PARTITION_PLAN.json
HOME_KEYS_SURFACE.json
HOME_MCP_SURFACE.json
HOME_ROUTER_SURFACE.json
HOME_PROVIDER_LADDER_HINTS.json
HOME_LITELLM_SURFACE.json
HOME_PROFILES_SURFACE.json
HOME_TMUX_WORKFLOW_SURFACE.json
HOME_REFERENCES.json
HOME_SQLITE_SCHEMA.json (schema only; no row data)
H_COVERAGE_REPORT.json

## Hard rules
JSON only, ASCII only.
Do not output secret values.
Do not output arbitrary file contents.
Every item must include path and line_range (or byte_range if binary).
If file is binary or sqlite: extract metadata only (and schema, if sqlite).

## H0: Inventory + partition plan (mandatory)
ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.

TARGET PATHS (expand ~):
- ~/.dopemux
- ~/.config/dopemux
- ~/.config/taskx
- ~/.config/litellm
- ~/.config/mcp

OUTPUT 1: HOME_CONTROL_INVENTORY.json
For each file under these roots:
- path
- size_bytes
- last_modified
- file_kind: dir|text|json|yaml|toml|sqlite|binary|unknown
- sha256 if text and <= 1MB else null
- first_nonempty_line if text and <= 200KB else null
- contains_tokens[] from:
  ["mcp","litellm","router","provider","model","taskx","profile","session","hook","tmux","compose","dashboard","db","sqlite","postgres","token","key","secret"]

OUTPUT 2: HOME_CONTROL_PARTITION_PLAN.json
Create deterministic partitions with explicit file path lists:
H1_KEYS_AND_REFERENCES
H2_MCP
H3_ROUTER_AND_PROVIDER_LADDERS
H4_LITELLM
H5_PROFILES_AND_SESSIONS
H6_TMUX_AND_WORKFLOW
H7_SQLITE_AND_STATE_DB_META

RULES:
- Partitioning by path and filename heuristics only.
- JSON only.

## H1: Keys + references (where home config points into repo/world)
Outputs
HOME_KEYS_SURFACE.json
HOME_REFERENCES.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- any text/json/yaml/toml file in partitions H1/H3/H4

TASK 1: HOME_KEYS_SURFACE.json
Extract key structure only:
- For YAML/TOML/JSON:
  - top-level keys
  - nested key paths up to depth=6
  - do not include values unless value is boolean/number or a safe enum word
- For non-structured text:
  - extract lines that look like KEY=VALUE but output only KEY and redacted indicator

Each item:
- path, line_range
- key_paths[] (e.g., "mcp.servers.local_files.command")
- value_kind for each path: string|number|bool|list|object|unknown
- safe_value if bool/number else null

TASK 2: HOME_REFERENCES.json
Extract literal references to:
- file paths
- URLs
- command invocations
- environment variable names
- sockets/ports (e.g., :4000)
For each reference:
- ref_kind: path|url|command|env|port
- value (literal, but redact secrets)
- path, line_range, excerpt <= 6 lines

REDACTION:
- If value contains "token", "key", "secret", "pass", or looks like a long random string, output "***REDACTED***"
- Never output private keys or credential blobs.

JSON only.

## H2: MCP surface (home)
Output
HOME_MCP_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- ~/.dopemux/mcp_config.json
- ~/.dopemux/mcp-tools/**
- ~/.config/mcp/** (all text configs)
- any file containing token "mcp"

Extract:
- server definitions (name, command, args, env keys only)
- allowlists/denylists
- root directories and project allowlists
- proxy endpoints if present

Each server item:
- server_name
- command
- args[]
- env_keys[]
- path, line_range, excerpt <= 20 lines

Each policy item:
- policy_kind (allowlist/denylist/roots/projects)
- values (paths ok, redact sensitive)
- path, line_range, excerpt <= 20 lines

JSON only.

## H3: Router + provider ladders (home)
Outputs
HOME_ROUTER_SURFACE.json
HOME_PROVIDER_LADDER_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- ~/.dopemux/**router**
- ~/.dopemux/**platform**
- ~/.dopemux/**claude-code-router**
- ~/.dopemux/**dope-brainz-router**
- ~/.config/dopemux/config.yaml
- ~/.config/dopemux/dopemux.toml
- ~/.config/taskx/**

TASK 1: HOME_ROUTER_SURFACE.json
Extract blocks that define:
- models
- reasoning effort
- trust levels / project trust
- routing conditions
- default providers
- endpoint base URLs (redacted if includes tokens)

Include:
- detected_keys[]
- excerpt <= 40 lines
- path, line_range

TASK 2: HOME_PROVIDER_LADDER_HINTS.json
Extract ordered lists of providers/models/fallbacks:
- ordered_items[]
- where they appear (path, line_range, excerpt <= 20 lines)

JSON only.

## H4: LiteLLM surfaces (home)
Outputs
HOME_LITELLM_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- ~/.dopemux/litellm/**
- ~/.config/litellm/**

Extract:
- model lists
- routing rules
- logging/callbacks
- db config keys (redact values)
- ports/endpoints
- allowlists

Each block:
- path, line_range, excerpt <= 60 lines
- detected_keys[]
- any env var keys

JSON only.

## H5: Profiles + sessions (home)
Outputs
HOME_PROFILES_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- ~/.dopemux/profiles/**
- ~/.dopemux/sessions/**
- ~/.config/dopemux/profiles/**

Extract:
- profile file names and key paths (no sensitive values)
- session metadata (file names, timestamps)
- any references to workflows, servers, models, task packets

Each item:
- item_kind: profile|session|cache
- path
- size_bytes
- detected_tokens[] from ["workflow","task","packet","model","provider","server","mcp","litellm"]
- for text: key_paths[] up to depth=5
- for json: top-level keys

JSON only.

## H6: Tmux + workflow helpers (home)
Outputs
HOME_TMUX_WORKFLOW_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE:
- ~/.dopemux/tmux-layout.sh
- any shell scripts under ~/.dopemux/** that contain "tmux" or "worktree" or "agent"

Extract:
- tmux session/window/pane definitions
- commands executed in panes
- references to repo paths or services
- any implicit orchestration steps

Each chain:
- chain_id
- commands[] (literal)
- path, line_range, excerpt <= 40 lines

JSON only.

## H7: SQLite + state DB metadata (home) (NO ROWS)
Outputs
HOME_SQLITE_SCHEMA.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE (likely from your inventory):
- ~/.dopemux/context.db
- ~/.dopemux/global_index.sqlite
- any other *.db / *.sqlite found

RULES:
- Do NOT read row data.
- Only extract schema metadata:
  - list tables
  - list columns per table
  - list indexes
  - list triggers
  - schema_version if present

Each db:
- path
- size_bytes
- tables[]:
  - name
  - columns[] {name,type,notnull,pk,default}
  - indexes[] (name, columns)
  - triggers[] (name, table)
- errors[] if unable to read schema

JSON only.

## H9: Merge + QA
Outputs
normalized outputs under H_home_control_plane/norm/
H_COVERAGE_REPORT.json
ROLE: Mechanical normalizer. No reasoning. JSON only. ASCII only.

INPUTS: all raw outputs H0-H7.

MERGE RULES:
- dedupe by (path, line_range, sha256(excerpt))
- stable sort by path then start line
- ensure each normalized output includes:
  - artifact_type
  - generated_at_local
  - inputs[] (file list)
  - items[]

QA OUTPUT: H_COVERAGE_REPORT.json
Include:
- expected_artifacts list
- present_artifacts list
- missing_artifacts list
- item_counts per artifact
- redaction_count
- db_count and table_count summary

JSON only.
