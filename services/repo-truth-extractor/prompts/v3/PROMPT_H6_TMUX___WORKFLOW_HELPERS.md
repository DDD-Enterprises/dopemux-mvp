# Phase H6: Home TMUX + Workflow Helpers Surface

Goal:
- Extract tmux session definitions, scripts, aliases, and helper commands that appear to bootstrap Dopemux/TaskX workflows.

Outputs:
- HOME_TMUX_WORKFLOW_SURFACE.json

HOME_TMUX_WORKFLOW_SURFACE.json:
{
  "surface_version": "H6.v1",
  "generated_at": "<iso8601>",
  "workflows": [
    {
      "name": "<string>",
      "kind": "<tmux|shell|alias|script>",
      "entrypoint": "<string>",
      "paths_involved": ["<path>"],
      "commands": ["<command string>"],
      "evidence": {"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}
