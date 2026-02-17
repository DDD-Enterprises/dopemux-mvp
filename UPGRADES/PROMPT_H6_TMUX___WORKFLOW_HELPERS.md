# PROMPT_H6 — HOME tmux + workflow helpers (SAFE MODE)

ROLE: Forensic extractor.
GOAL:
Extract home-level tmux scripts/layouts and any helper scripts that encode workflows.

HARD RULES:
- Only capture literal commands if they are not secrets.
- Redact env exports that contain secret-looking values.

OUTPUT: HOME_TMUX_WORKFLOW_SURFACE.json
{
  "artifact": "HOME_TMUX_WORKFLOW_SURFACE",
  "generated_at": "<iso8601>",
  "artifacts": [
    {
      "path": "<absolute>",
      "type": "tmux_conf|layout_script|helper_script|other",
      "commands": ["<literal commands redacted as needed>"],
      "services_referenced": ["conport","serena","dope-context","litellm","taskx","other"],
      "evidence": "<path/section>"
    }
  ]
}
