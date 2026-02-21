# PROMPT_S1 - OPUS MCP TO HOOKS MIGRATION PLAN (evidence-bounded)

ROLE: Migration planner (audit-grade, conservative).
MODE: Evidence-bounded synthesis. No excavation.

GOAL:
- Produce a staged MCP-to-hooks migration plan using only supplied synthesis artifacts.
- Preserve boundary controls and avoid behavioral drift.

OUTPUTS:
- S1_MCP_TO_HOOKS_MIGRATION_PLAN.md

HARD RULES:
1) Do not rescan the repo or invent components.
2) Every non-trivial claim must end with:
   EVIDENCE: <artifact_filename>#<section_heading_or_anchor>
3) If evidence is missing, write UNKNOWN and exclude the candidate from execution steps.
4) Prefer minimal mechanical moves. No refactors.
5) All no-go gates must tie to R8 risk IDs and R7 conflicts when relevant.

INPUTS (required):
- R0_CONTROL_PLANE_TRUTH_MAP.md
- R3_TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
- R6_PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- R7_CONFLICT_LEDGER.md
- R8_RISK_REGISTER_TOP20.md

INPUTS (optional):
- REPO_MCP_SERVER_DEFS.json
- REPO_HOOKS_SURFACE.json
- REPO_MCP_PROXY_SURFACE.json
- REPO_ROUTER_SURFACE.json
- FEATURE_INDEX_MERGED.json

OUTPUT FORMAT (write the full content of S1_MCP_TO_HOOKS_MIGRATION_PLAN.md):
1) Scope and Constraints
- Summarize objective boundaries and guardrails.

2) Candidate Inventory
- Include only candidates with evidence for both current MCP mechanism and target hook surface.
- Mark unsupported candidates as UNKNOWN with missing evidence references.

3) Plan Stages
- Entry criteria (evidence-based)
- Steps (mechanical)
- Verification suggestions
- Rollback path

4) No-Go Triggers Table
- Columns: trigger, linked risk_id (R8), linked conflict_id (R7 if applicable), evidence.

5) UNKNOWN and Missing Evidence Register
- Explicit unresolved items and required artifacts.
