Phase H goal
Extract the home-resident control plane that Dopemux depends on, without leaking secrets:
MCP tools + server configs
routers (claude-code-router, dope-brainz-router, etc.)
litellm configs
hooks enablement state
profiles overlays
tmux orchestration
SQLite schema only (no data)
Outputs are evidence indexes only.
Model
Gemini Flash 3 (Antigravity)
Hard rules
JSON only, ASCII only.
No interpretation.
Every item has path and line_range where possible.
Deterministic ordering by path, then line_range.
Strict allowlist: only the paths listed below.
Home allowlist (observed)
From your listing:
Roots
~/.dopemux/**
~/.config/dopemux/**
Key paths (priority include)
~/.dopemux/mcp_config.json
~/.dopemux/mcp-tools/**
~/.dopemux/*router/**
~/.dopemux/claude-code-router/**
~/.dopemux/dope-brainz-router/**
~/.dopemux/claude-platform/** (if used for routing/policy)
~/.dopemux/litellm/**
~/.dopemux/hook_status.json
~/.dopemux/profiles/**
~/.dopemux/tmux-layout.sh
~/.config/dopemux/config.yaml
~/.config/dopemux/dopemux.toml
~/.config/dopemux/profiles/**
State stores (schema-only)
~/.dopemux/context.db
~/.dopemux/global_index.sqlite
Redaction policy (deterministic)
When extracting any config content:
If a key name or surrounding text contains any of:
token, key, secret, password, api, auth, bearer, cookie, credential
then output the value as "REDACTED".
If a value matches patterns:
PEM blocks (-----BEGIN)
JWT-ish (xxxxx.yyyyy.zzzzz)
long base64 blobs
32+ hex strings
output "REDACTED_PATTERN".
For env files: output variable names only, never values.
H0: Home inventory + partition plan
Outputs
HOME_CONTROL_INVENTORY.json
HOME_CONTROL_PARTITION_PLAN.json
ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.

ALLOWLIST ROOTS:
- ~/.dopemux/**
- ~/.config/dopemux/**

OUTPUT 1: HOME_CONTROL_INVENTORY.json
For each file under allowlist roots:
- path
- size_bytes
- last_modified (if available)
- sha256 (if available)
- kind by extension only: json|yaml|toml|db|sqlite|sh|md|env|other
- is_sqlite=true if filename ends with .db or .sqlite
- is_probably_state=true if path contains "/sessions/" OR filename contains "cache"

OUTPUT 2: HOME_CONTROL_PARTITION_PLAN.json
Create deterministic partitions:
H1_KEYS_AND_GLOBAL =
  ~/.dopemux/mcp_config.json +
  ~/.dopemux/hook_status.json +
  ~/.dopemux/instances_cache.json +
  ~/.config/dopemux/config.yaml +
  ~/.config/dopemux/dopemux.toml +
  ~/.config/dopemux/dashboard.json

H2_MCP_TOOLS =
  ~/.dopemux/mcp-tools/**

H3_ROUTERS =
  ~/.dopemux/claude-code-router/** +
  ~/.dopemux/dope-brainz-router/** +
  ~/.dopemux/claude-platform/**

H4_LITELLM =
  ~/.dopemux/litellm/**

H5_PROFILES =
  ~/.dopemux/profiles/** +
  ~/.config/dopemux/profiles/**

H6_TMUX_AND_WORKFLOW =
  ~/.dopemux/tmux-layout.sh

H7_STATE_SCHEMA_ONLY =
  ~/.dopemux/context.db +
  ~/.dopemux/global_index.sqlite

RULES:
- If any partition has > 30 files, split into subpartitions of 20 files each
  named like H2_MCP_TOOLS__01, H2_MCP_TOOLS__02, etc.
- Order files within partition by path ascending.
- JSON only.
H1: Keys + config surface (safe key paths)
Outputs
HOME_KEYS_SURFACE.<partition_id>.json
HOME_REFERENCES.<partition_id>.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- HOME_CONTROL_PARTITION_PLAN.json
PARAM: partition_id = <H1_KEYS_AND_GLOBAL>

SCOPE: files in that partition only.

TASK 1: HOME_KEYS_SURFACE.<partition_id>.json
For JSON/YAML/TOML files:
- extract key paths only (no raw values)
- include path and line_range if available
For any env-like file:
- extract variable NAMES only

TASK 2: HOME_REFERENCES.<partition_id>.json
Extract literal references to:
- MCP server/tool names ("mcp", "server", "tool", "mcp_servers")
- commands/args ("command", "args", "npx", "uvx", "docker", "compose")
- endpoints/ports ("http", "localhost", port numbers)
- file path references ("~/", "/Users/", ".dopemux/", ".config/")
For each:
- ref_type
- excerpt <= 4 lines
- path, line_range

REDACTION:
- apply deterministic redaction policy to any value-like substrings in excerpt.

RULES:
- JSON only.
- Deterministic ordering.
H2: MCP tools surface (commands + args + env names)
Outputs
HOME_MCP_SURFACE.<partition_id>.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- HOME_CONTROL_PARTITION_PLAN.json
PARAM: partition_id = <H2_MCP_TOOLS or a subpartition>

SCOPE: files in that partition only.

Extract:
- tool_name / server_name if present
- command
- args
- env var NAMES referenced
- endpoints/ports if present (keep unless credential-like)
For each item include:
- path, line_range, excerpt <= 6 lines

REDACTION:
- redact any secret-like values per policy.

RULES:
- JSON only.
- No inference.
H3: Router surface (provider ladders, policies, fallbacks)
Outputs
HOME_ROUTER_SURFACE.<partition_id>.json
HOME_PROVIDER_LADDER_HINTS.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- HOME_CONTROL_PARTITION_PLAN.json
PARAM: partition_id = <H3_ROUTERS or a subpartition>

SCOPE: files in that partition only.

TASK 1: HOME_ROUTER_SURFACE.<partition_id>.json
Extract blocks containing any tokens:
router, routing, fallback, policy, ladder, model, provider, tier, allowlist, denylist
Emit:
- path, line_range, excerpt <= 8 lines

TASK 2: HOME_PROVIDER_LADDER_HINTS.json
Extract explicit ordered lists that look like model/provider ladders:
- arrays/lists of providers/models
Emit:
- ladder_id, items[], path, line_range

REDACTION:
- redact credentials/tokens.

RULES:
- JSON only.
- No inference.
H4: LiteLLM surface (db, spend, model map keys)
Outputs
HOME_LITELLM_SURFACE.<partition_id>.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- HOME_CONTROL_PARTITION_PLAN.json
PARAM: partition_id = <H4_LITELLM or a subpartition>

SCOPE: files in that partition only.

Extract from litellm configs:
- model map keys
- router settings (fallbacks, retries, timeouts) if present
- database settings (db type, path/url keys) but redact credentials
- spend tracking toggles
Include:
- excerpt <= 8 lines with path + line_range

RULES:
- JSON only.
- No inference.
H5: Profiles overlays (what changes behavior by persona/profile)
Outputs
HOME_PROFILES_SURFACE.<partition_id>.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

INPUTS:
- HOME_CONTROL_PARTITION_PLAN.json
PARAM: partition_id = <H5_PROFILES or a subpartition>

SCOPE: files in that partition only.

Extract:
- profile ids/names
- key paths present in each profile (no values)
- any references to services, tools, mcp, hooks, routers, providers
Include:
- path, line_range, excerpt <= 6 lines where references occur

REDACTION:
- redact secret-like values.

RULES:
- JSON only.
- No inference.
H6: Tmux/workflow orchestration (what’s launched)
Outputs
HOME_TMUX_WORKFLOW_SURFACE.json
ROLE: Mechanical extractor. No reasoning. JSON only. ASCII only.

SCOPE INCLUDE ONLY:
- ~/.dopemux/tmux-layout.sh

Extract:
- commands executed
- referenced paths
- service/process names
- ports/endpoints mentioned
Emit each command line as an item with:
- path, line_range, excerpt <= 2 lines

RULES:
- JSON only.
- No inference.
H7: SQLite schema-only (no data)
Outputs
HOME_SQLITE_SCHEMA.json
ROLE: Mechanical schema extractor. No reasoning. JSON only. ASCII only.

SCOPE INCLUDE ONLY:
- ~/.dopemux/context.db
- ~/.dopemux/global_index.sqlite

Extract SQLite schema only:
- tables
- indexes
- triggers
- views
- PRAGMA user_version if available

OUTPUT: HOME_SQLITE_SCHEMA.json
For each object:
- name
- type
- sql definition string
- source file path

RULES:
- Do not extract table contents.
- Do not run SELECT *.
- JSON only.
H8: Merge + QA coverage
Outputs
HOME_KEYS_SURFACE.json
HOME_REFERENCES.json
HOME_MCP_SURFACE.json
HOME_ROUTER_SURFACE.json
HOME_PROVIDER_LADDER_HINTS.json
HOME_LITELLM_SURFACE.json
HOME_PROFILES_SURFACE.json
HOME_TMUX_WORKFLOW_SURFACE.json
HOME_COVERAGE_REPORT.json
ROLE: Mechanical normalizer. No reasoning. JSON only. ASCII only.

INPUTS:
- all HOME_*.<partition_id>.json artifacts
- HOME_CONTROL_INVENTORY.json
- HOME_CONTROL_PARTITION_PLAN.json

MERGE:
- concatenate by artifact type
- dedupe by (path, line_range, hash(excerpt or key_path))
- stable sort by path then line_range

QA OUTPUT: HOME_COVERAGE_REPORT.json
Include:
- total_files (from inventory)
- files_processed (count files appearing in any merged artifact)
- partitions_completed list
- files_missing_all (in inventory but absent from any artifact)

RULES:
- JSON only.
- No interpretation.
Phase H success signals
You are done when:
HOME_CONTROL_INVENTORY.json exists
HOME_CONTROL_PARTITION_PLAN.json exists
merged HOME_* artifacts exist
HOME_COVERAGE_REPORT.json shows low or zero files_missing_all for non-state files
No decisions.
