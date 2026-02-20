# PHASE A1 — INSTRUCTION SURFACES (REPO)
Model: Gemini Flash 3
Goal: Produce REPO_INSTRUCTION_SURFACE.json + REPO_INSTRUCTION_REFERENCES.json

Hard rules:
- Extract ONLY what is explicitly present in files.
- Every extracted item MUST include evidence: {path, anchor_excerpt<=200 chars}.
- No guessing. If unclear, record UNKNOWN with evidence showing ambiguity.

Inputs:
- Partition content from A0 P0 partitions: instruction docs, agent files, custom instructions directories.

Task:
1) Build REPO_INSTRUCTION_SURFACE.json:
   Identify all instruction-bearing files and normalize into:
   - instruction_sources[] items:
     - id (stable, e.g., INSTR_0001)
     - path
     - kind (one of: "claude_system", "agent_profile", "tooling_instructions", "prompt_template", "workflow_playbook", "other")
     - scope (repo-wide / project-specific / tool-specific)
     - referenced_tools (list of strings found literally: e.g., "conport", "serena", "mcp", "litellm", "taskx")
     - declared_behaviors (list of short literal statements, each with anchor_excerpt)
     - declared_boundaries (list, each with anchor_excerpt)
     - declared_dataflows (list, each with anchor_excerpt)
   Determinism: sort by path, then by first appearance.

2) Build REPO_INSTRUCTION_REFERENCES.json:
   A cross-reference map of “instruction mentions -> targets”.
   Extract literal references to:
   - services (conport, serena, dope-context, dashboard, orchestrator, proxy)
   - MCP servers/tools
   - router/provider ladders
   - scripts/commands
   Output:
   - references[]:
     - ref_type ("service"|"command"|"file_path"|"env_var"|"mcp_server"|"model"|"other")
     - ref_value (literal string)
     - source_path
     - anchor_excerpt

Output files:
- REPO_INSTRUCTION_SURFACE.json
- REPO_INSTRUCTION_REFERENCES.json
