# PHASE A4 — HOOKS + IMPLICIT TRIGGERS (REPO)
Model: Gemini Flash 3
Goal: Produce REPO_HOOKS_SURFACE.json + REPO_IMPLICIT_BEHAVIOR_HINTS.json

Hard rules:
- Hook map must be command-literal, not interpreted.
- Evidence required: {path, anchor_excerpt}.
- If a hook calls a script, record the call and the script path as a coupling edge.

Inputs:
- .githooks/**, scripts/**, Makefile targets that run automatically, CI workflows, installer scripts.

Task:
1) REPO_HOOKS_SURFACE.json:
   - triggers[]:
     - trigger_type (git_hook|ci|make_target|installer|startup_script|other)
     - trigger_name (pre-commit, post-checkout, workflow name, etc.)
     - commands[] (literal lines)
     - touches_paths[] (literal paths mentioned)
     - writes_state (bool if explicit)
     - evidence

2) REPO_IMPLICIT_BEHAVIOR_HINTS.json:
   Extract “implicit behavior language” from instruction/docs/config that suggests automatic actions:
   - “auto”, “on startup”, “on run”, “will generate”, “writes to”, “creates”, “ensures dirs”
   Each hint:
   - hint_text (short)
   - source_path + anchor_excerpt
