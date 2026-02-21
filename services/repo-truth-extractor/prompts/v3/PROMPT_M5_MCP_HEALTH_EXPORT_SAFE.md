Goal: M5_MCP_HEALTH_EXPORT_SAFE.json

Prompt:
- Task: export MCP health summary without network calls.
- Include:
  - MCP server definitions (name, command, args count)
  - env keys only (never env values)
  - file/config presence checks and parseability status
  - implementer metadata: implementer="GPT-5.3-Codex", authority="Codex CLI/Desktop"
- Hard rules:
  - Do not perform network probes.
  - Do not expose secrets or values.
  - Keep output bounded; include truncation markers when capped.
