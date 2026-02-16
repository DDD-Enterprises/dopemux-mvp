# PROMPT_H2_MCP_SURFACE
Goal: extract HOME MCP server + tool surface (SAFE MODE)
Model: Gemini Flash (preferred)

## Mission
Using ONLY allowlisted home control plane files:
- ~/.dopemux/
- ~/.config/mcp/
- ~/.config/dopemux/
- ~/.config/litellm/  (ONLY if referenced by MCP configs)
- ~/.config/taskx/    (ONLY if referenced by MCP configs)

Extract the complete HOME MCP surface:
1) Server definitions (name, command, args, cwd, enabled/disabled, transport hints)
2) Tool definitions (if present): tool name, inputs schema hints, permissions/scopes
3) Environment dependencies (env var NAMES only; values redacted)
4) Filesystem access and safety posture (allowlists, roots, path scopes) if explicit
5) References between MCP config and dopemux router/profiles if explicit

## Hard rules
- Do not read outside allowlist roots.
- No secrets: redact any values that look like keys/tokens/passwords/headers.
- Evidence required for every extracted item:
  HOMECTRL: <path>#Lx-Ly  (or) HOMECTRL: <path>:<unique_excerpt<=12_words>
- Do not infer server existence. Only extract if literally present.
- If configs are truncated, mark UNKNOWN and cite truncation anchor.
- Output JSON only.

## Output artifacts (JSON only)
Produce:
1) HOME_MCP_SURFACE.json
2) HOME_MCP_ENV_DEPS.json
3) HOME_MCP_FILESYSTEM_SCOPE.json

### 1) HOME_MCP_SURFACE.json
{
  "artifact": "HOME_MCP_SURFACE",
  "generated_at": "<iso8601>",
  "servers": [
    {
      "name": "<server_name>",
      "enabled": true,
      "command": "<literal>",
      "args": ["<literal>", "..."],
      "cwd": "<literal_or_null>",
      "transport": "stdio|http|ws|unknown",
      "timeout_ms": "<literal_or_null>",
      "restart_policy": "<literal_or_null>",
      "notes": ["..."],
      "evidence": ["HOMECTRL: <path>#Lx-Ly"]
    }
  ],
  "tools": [
    {
      "server": "<server_name>",
      "tool": "<tool_name>",
      "input_schema_hint": "<short literal or UNKNOWN>",
      "output_schema_hint": "<short literal or UNKNOWN>",
      "permissions_hint": "<literal or UNKNOWN>",
      "evidence": ["HOMECTRL: <path>#Lx-Ly"]
    }
  ],
  "unknowns": [
    {"area": "tools", "reason": "No tool schema present in provided files", "evidence": ["HOMECTRL: <path>#..."]}
  ]
}

### 2) HOME_MCP_ENV_DEPS.json
{
  "artifact": "HOME_MCP_ENV_DEPS",
  "generated_at": "<iso8601>",
  "env_vars": [
    {
      "name": "OPENAI_API_KEY",
      "used_by": ["<server_name>"],
      "evidence": ["HOMECTRL: <path>#Lx-Ly"],
      "risk": "HIGH|MED|LOW"
    }
  ],
  "notes": [
    "Values redacted by rule; names only."
  ]
}

### 3) HOME_MCP_FILESYSTEM_SCOPE.json
{
  "artifact": "HOME_MCP_FILESYSTEM_SCOPE",
  "generated_at": "<iso8601>",
  "scopes": [
    {
      "server": "<server_name>",
      "scope_type": "allowlist|denylist|root|unknown",
      "paths": ["<literal_path>", "..."],
      "evidence": ["HOMECTRL: <path>#Lx-Ly"]
    }
  ],
  "unknowns": [
    {"server": "<server_name>", "reason": "No filesystem scope declared in config"}
  ]
}

## Normalization + determinism
- Sort servers by name.
- Sort tools by (server, tool).
- Preserve literal command/args order.
- Keep literals as seen (do not expand ~ unless BOTH raw+expanded are explicit).

## Redaction rules
Never output:
- token-like strings
- api key values
- password values
- Authorization headers
Replace with "[REDACTED]" if present in content.

## Finish
Emit ONLY the three JSON artifacts.
No prose.
No markdown fences.
