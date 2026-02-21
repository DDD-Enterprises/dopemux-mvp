# PROMPT_W3 — Workflow artifacts + state surfaces

ROLE: Workflow plane extractor.
GOAL: Identify workflow outputs (logs, DBs, caches, run dirs) and state coupling points.

OUTPUTS:
  • WORKFLOW_STATE_SURFACE.json
    - state_items[]: {path, type(log/db/cache/run_dir/config), writer, reader, retention_hint, evidence_refs[]}
  • WORKFLOW_COUPLING_POINTS.json
    - couplings[]: {kind(home_state/repo_state/env/mcp/compose), description, evidence_refs[]}

RULES:
  • retention_hint must be UNKNOWN unless explicitly stated.
  • Prefer listing concrete paths and filenames with supporting evidence.
