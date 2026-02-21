# PROMPT_H8_NORMALIZE___MERGE___CANONICALIZE
Goal: merge all Phase H raw artifacts into deterministic normalized artifacts (SAFE MODE)
Model: Gemini Flash (preferred) OR Grok (ok) - low creativity

## Inputs
You will be given:
- all Phase H raw JSON outputs from prior steps (H0–H7), potentially chunked
- (optional) a partition manifest file from H0

You must NOT rescan the filesystem. Operate ONLY on provided artifacts.

## Mission
1) Validate + normalize JSON structures:
- stable key ordering
- stable list sorting (when order is not semantically meaningful)
- canonicalize paths consistently (preserve "~" if present; redact username if absolute /Users/<name>/...)
- deduplicate repeated items across chunks
2) Produce a deterministic "HOME_CONTROL_PLANE_NORM" pack:
- one merged file per major artifact family expected by Phase R
3) Produce a merge report:
- counts, duplicates removed, missing expected families, and SAFE MODE redaction flags
4) Produce a schema-lite QA summary:
- for each output, include "required_fields_ok": true/false and list missing fields

## Hard rules
- SAFE MODE: do not output secrets; propagate redactions forward.
- Every merged item must retain provenance via "sources" array:
  - "sources": [{"artifact":"HOME_*_RAW","path":"<file>", "evidence":["HOMECTRL: ..."]}]
- If an item lacks evidence, keep it but label:
  - "evidence_status": "MISSING"
- If two chunks conflict on a literal value, keep BOTH as "variants" and do NOT resolve.

## Required normalized outputs (JSON only)
Produce these files as JSON objects:

1) HOME_MCP_SURFACE.json
2) HOME_ROUTER_SURFACE.json
3) HOME_PROVIDER_LADDER_HINTS.json
4) HOME_LITELLM_SURFACE.json
5) HOME_PROFILES_SURFACE.json
6) HOME_TMUX_WORKFLOW_SURFACE.json
7) HOME_SQLITE_SCHEMA.json

Also produce:
8) HOME_NORM_MERGE_REPORT.json

### Canonical schemas

#### 1) HOME_MCP_SURFACE.json
{
  "artifact": "HOME_MCP_SURFACE",
  "generated_at": "<iso8601>",
  "items": [
    {
      "server_name": "<name_or_UNKNOWN>",
      "kind": "mcp_server|tool|proxy|unknown",
      "command": "<literal_or_UNKNOWN>",
      "args": ["<literal>"],
      "env_vars": ["<NAME_ONLY>"],
      "config_paths": ["<paths>"],
      "redactions": ["<what_was_redacted>"],
      "sources": [{"artifact":"...","path":"...","evidence":["HOMECTRL: ..."]}],
      "evidence_status": "OK|MISSING"
    }
  ],
  "unknowns": [{"area":"...", "reason":"..."}]
}

#### 2) HOME_ROUTER_SURFACE.json
{
  "artifact": "HOME_ROUTER_SURFACE",
  "generated_at": "<iso8601>",
  "routers": [
    {
      "router_id": "<id_or_UNKNOWN>",
      "type": "<litellm|claude_router|dopemux_router|unknown>",
      "config_paths": ["<file>"],
      "providers": ["openai","anthropic","xai","google","unknown"],
      "model_ladders": [
        {
          "ladder_id": "<id_or_UNKNOWN>",
          "order": [{"provider":"...","model":"..."}],
          "conditions": ["<literal_or_UNKNOWN>"],
          "sources": [{"artifact":"...","path":"...","evidence":["HOMECTRL: ..."]}],
          "evidence_status": "OK|MISSING"
        }
      ],
      "sources": [{"artifact":"...","path":"...","evidence":["HOMECTRL: ..."]}],
      "evidence_status": "OK|MISSING"
    }
  ],
  "unknowns": []
}

#### 3) HOME_PROVIDER_LADDER_HINTS.json
{
  "artifact": "HOME_PROVIDER_LADDER_HINTS",
  "generated_at": "<iso8601>",
  "hints": [
    {
      "hint": "<literal>",
      "scope": "router|profile|mcp|unknown",
      "sources": [{"artifact":"...","path":"...","evidence":["HOMECTRL: ..."]}],
      "evidence_status": "OK|MISSING"
    }
  ]
}

#### 4) HOME_LITELLM_SURFACE.json
{
  "artifact": "HOME_LITELLM_SURFACE",
  "generated_at": "<iso8601>",
  "configs": [
    {
      "path": "<file>",
      "format": "<yaml|json|toml|env|other>",
      "routing": {"has_router_rules":"<bool_or_UNKNOWN>"},
      "logging": {"request_logging":"<bool_or_UNKNOWN>"},
      "env_vars": ["<NAME_ONLY>"],
      "datastores": [{"type":"sqlite|postgres|unknown","path_or_dsn":"<literal_or_REDACTED_or_UNKNOWN>"}],
      "sources": [{"artifact":"...","path":"...","evidence":["HOMECTRL: ..."]}],
      "evidence_status": "OK|MISSING"
    }
  ]
}

#### 5) HOME_PROFILES_SURFACE.json
{
  "artifact": "HOME_PROFILES_SURFACE",
  "generated_at": "<iso8601>",
  "profiles": [
    {
      "profile_id": "<id>",
      "path": "<file_or_dir>",
      "defaults": [{"key":"...","value_literal_if_safe":"..."}],
      "safety": [{"key":"...","value_literal_if_safe":"..."}],
      "sources": [{"artifact":"...","path":"...","evidence":["HOMECTRL: ..."]}],
      "evidence_status": "OK|MISSING"
    }
  ],
  "default_profile_pointer": {"value_literal_if_safe":"<id_or_UNKNOWN>","sources":[...]}
}

#### 6) HOME_TMUX_WORKFLOW_SURFACE.json
{
  "artifact": "HOME_TMUX_WORKFLOW_SURFACE",
  "generated_at": "<iso8601>",
  "entrypoints": [
    {
      "kind": "script|make_target|alias|function|unknown",
      "invocation": "<literal_command>",
      "references": ["taskx","dopemux","docker","mcp","litellm","unknown"],
      "sources": [{"artifact":"...","path":"...","evidence":["HOMECTRL: ..."]}],
      "evidence_status": "OK|MISSING"
    }
  ],
  "layouts": [
    {
      "name": "<name_or_UNKNOWN>",
      "sessions": [{"session":"...","windows":[{"window":"...","panes":[{"pane":"...","command":"..."}]}]}],
      "sources": [{"artifact":"...","path":"...","evidence":["HOMECTRL: ..."]}],
      "evidence_status": "OK|MISSING"
    }
  ]
}

#### 7) HOME_SQLITE_SCHEMA.json
{
  "artifact": "HOME_SQLITE_SCHEMA",
  "generated_at": "<iso8601>",
  "db_files": [{"path":"...","size":0,"mtime":"...","role_hint":"...","sources":[...]}],
  "schema_sources": [{"source_path":"...","tables":["..."],"indexes":["..."],"triggers":["..."],"sources":[...]}],
  "reference_edges": [{"from_config":"...","to_db":"...","sources":[...]}],
  "unknowns": []
}

#### 8) HOME_NORM_MERGE_REPORT.json
{
  "artifact": "HOME_NORM_MERGE_REPORT",
  "generated_at": "<iso8601>",
  "inputs_seen": ["<raw_file_paths>"],
  "outputs_written": ["HOME_MCP_SURFACE.json", "..."],
  "counts": {"HOME_MCP_SURFACE.items":0, "HOME_ROUTER_SURFACE.routers":0, "...":0},
  "duplicates_removed": [{"key":"<stable_identity_key>","count":0}],
  "conflicts_preserved": [{"area":"<name>","variants":2}],
  "missing_expected_families": ["HOME_PROVIDER_LADDER_HINTS"],
  "redaction_flags": [{"file":"<path>","pattern":"<secret_like>","action":"REDACTED"}],
  "schema_checks": [{"output":"HOME_MCP_SURFACE.json","required_fields_ok":true,"missing_fields":[]}]
}

## Determinism
- Sort all top-level lists by stable identity:
  - servers by server_name+command
  - profiles by profile_id
  - db_files by path
  - entrypoints by kind+invocation
- Keep *explicit* ladder order (do not sort ladder order arrays).

## Finish
Emit ONLY the 8 JSON objects (one per file), separated by:
===FILE: <filename>===
No markdown fences.
No prose.
