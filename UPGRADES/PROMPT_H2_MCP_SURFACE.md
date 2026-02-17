# PROMPT_H2 — HOME MCP surface (SAFE MODE)

ROLE: Forensic extractor.
GOAL:
Extract *home-side* MCP configuration surfaces: client configs, server registries, tool defs, endpoints, env wiring.

HARD RULES:
- Redact credentials, tokens, URLs containing credentials.
- Do not invent server names or capabilities. Only what is evidenced.

OUTPUT: HOME_MCP_SURFACE.json
{
  "artifact": "HOME_MCP_SURFACE",
  "generated_at": "<iso8601>",
  "configs": [
    {
      "path": "<absolute>",
      "format": "json|yaml|toml|other",
      "mcp_servers": [
        {
          "name": "<server id>",
          "command": "<string redacted if contains secret>",
          "args": ["<...>"],
          "env_keys": ["<ENV_KEY_ONLY>"],
          "notes": "<short>"
        }
      ],
      "client_settings": { "keys": ["<key names only>"] }
    }
  ],
  "inferred_graph": [
    { "client": "dopemux|taskx|other", "server": "<name>", "evidence": "<path/section>" }
  ]
}
