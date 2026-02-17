# PHASE A7 — TASKX SURFACES (REPO CONTROL PLANE)
Model: Gemini Flash 3
Goal: Produce REPO_TASKX_SURFACE.json

Hard rules:
- This is repo control plane only (no deep code tracing).
- Evidence required.

Inputs:
- .taskx/**, docs mentioning taskx, scripts calling taskx, config referencing taskx.

Task:
REPO_TASKX_SURFACE.json:
- taskx_files[] (paths)
- taskx_commands[] (literal commands seen: "taskx ...")
- packet_paths[] (literal)
- operator_instruction_injection_surfaces[] (files/commands that compile/inject instructions)
- env_vars[] (names)
- evidence everywhere
