# PROMPT_H6_TMUX___WORKFLOW_HELPERS
Goal: extract HOME tmux/layout/workflow helper truth (SAFE MODE)
Model: Gemini Flash (preferred)

## Mission
From allowlisted home roots:
- ~/.dopemux/tmux-layout.sh
- ~/.dopemux/**tmux**/**
- ~/.dopemux/sessions/**
- ~/.config/dopemux/dashboard.json (if relevant)
- any explicit workflow helper scripts under ~/.dopemux/**

Extract:
1) Workflow entrypoints: literal commands, scripts, make targets referenced
2) Tmux layouts: sessions, windows, panes, commands per pane (literal)
3) Environment expectations (env var names only)
4) Couplings: references to repo paths, worktrees, docker compose, mcp servers, taskx, litellm
5) Any explicit "bootstrap" sequences

## Hard rules
- No inference: only literal commands you see.
- Evidence per command.
- Do not output personal paths if they look sensitive; keep literal but allow "~" form if present. If only absolute is present, keep it but redact username segments: /Users/[REDACTED]/...

## Outputs (JSON only)
Produce:
1) HOME_TMUX_WORKFLOW_SURFACE.json
2) HOME_WORKFLOW_ENTRYPOINTS.json
3) HOME_WORKFLOW_ENV_DEPS.json

### 1) HOME_TMUX_WORKFLOW_SURFACE.json
{
  "artifact": "HOME_TMUX_WORKFLOW_SURFACE",
  "generated_at": "<iso8601>",
  "layouts": [
    {
      "name": "<layout_name_or_UNKNOWN>",
      "path": "<file>",
      "sessions": [
        {
          "session": "<name_or_UNKNOWN>",
          "windows": [
            {
              "window": "<name_or_index>",
              "panes": [
                {
                  "pane": "<index_or_UNKNOWN>",
                  "command": "<literal_command_or_UNKNOWN>",
                  "evidence": ["HOMECTRL: ..."]
                }
              ],
              "evidence": ["HOMECTRL: ..."]
            }
          ]
        }
      ],
      "evidence": ["HOMECTRL: ..."]
    }
  ]
}

### 2) HOME_WORKFLOW_ENTRYPOINTS.json
{
  "artifact": "HOME_WORKFLOW_ENTRYPOINTS",
  "generated_at": "<iso8601>",
  "entrypoints": [
    {
      "kind": "script|make_target|alias|function|unknown",
      "name": "<literal>",
      "invocation": "<literal_command>",
      "references": ["docker compose", "taskx", "dopemux", "litellm", "mcp", "unknown"],
      "evidence": ["HOMECTRL: ..."]
    }
  ]
}

### 3) HOME_WORKFLOW_ENV_DEPS.json
{
  "artifact": "HOME_WORKFLOW_ENV_DEPS",
  "generated_at": "<iso8601>",
  "env_vars": [
    {"name": "OPENAI_API_KEY", "used_in": ["<file>"], "evidence": ["HOMECTRL: ..."], "risk":"HIGH"}
  ]
}

## Determinism
- Sort layouts by name/path.
- Preserve pane command ordering as seen.

## Finish
Emit ONLY the three JSON artifacts.
No prose.
No markdown fences.
