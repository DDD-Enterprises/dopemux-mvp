# Phase H2: Home MCP Surface

Goal:
- Extract MCP server definitions, client configs, and any local MCP wiring present in home control-plane files.

Hard rules:
- Evidence-only.
- If MCP appears only as a hint (string mention) but no structured config is present, record as "hint_only".

Outputs:
- HOME_MCP_SURFACE.json

HOME_MCP_SURFACE.json:
{
  "surface_version": "H2.v1",
  "generated_at": "<iso8601>",
  "servers": [
    {
      "name": "<string>",
      "command": "<string or empty>",
      "args": ["<string>"],
      "env_keys": ["<ENV_VAR_NAME>"],
      "config_path": "<path>",
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "confidence": "<high|medium|low|hint_only>"
    }
  ],
  "clients": [
    {
      "name": "<string>",
      "config_path": "<path>",
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes": "<string>"
    }
  ],
  "notes": []
}
