# PROMPT: A2 - MCP Server Definitions

Phase: A
Step: A2

Outputs:
- REPO_MCP_SERVER_DEFS.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_MCP_SERVER_DEFS.json",
  "phase": "A",
  "step": "A2",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "mcp:<name>",
      "server_name": "...",
      "command": "...",
      "args": ["..."],
      "env": ["..."],
      "enabled": true,
      "source_path": "...",
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- MCP server definitions: name, command, args, env var names, enabled/disabled, cwd/root/allowed paths if present
- Any explicit per-server capabilities/notes
- Source locations and config keys
