# PROMPT: A3 - MCP Proxy Surface

Phase: A
Step: A3

Outputs:
- REPO_MCP_PROXY_SURFACE.json

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
  "artifact": "REPO_MCP_PROXY_SURFACE.json",
  "phase": "A",
  "step": "A3",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "mcp-proxy:<name_or_path>",
      "proxy_name": "...",
      "endpoint": "...",
      "upstream_targets": ["..."],
      "routes": ["..."],
      "auth_method": "...",
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
- Proxy config between clients/Dopemux and MCP servers
- Endpoints, routing rules, upstream targets, auth handling (only if explicit)
- Config search order hints only if explicit
