# PROMPT_S1 — OPUS MCP -> HOOKS MIGRATION IMPACT + PLAN (from Truth Pack)

ROLE: Opus Reviewer/Synthesist.
MODE: Migration planner under evidence constraints.

GOAL:
Design a safe, incremental MCP -> hooks migration plan (or a no-go recommendation),
grounded ONLY in Phase R truth artifacts and portability risks.

HARD RULES:
1) No repo rescans, no invented components.
2) Every migration claim MUST cite Phase R evidence:
   EVIDENCE: <filename>#<section>
3) Separate:
   - What is feasible now (IMPLEMENTED surfaces)
   - What requires new work (PLANNED or UNKNOWN)
4) No large refactors: propose minimal, mechanical steps.

INPUTS (required):
- R0 CONTROL_PLANE_TRUTH_MAP.md
- R5 WORKFLOWS_TRUTH_GRAPH.md
- R6 PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- R7 CONFLICT_LEDGER.md
- R8 RISK_REGISTER_TOP20.md
Optional:
- R3 TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md (to avoid bypassing guardrails)

DELIVERABLE:
Write MCP_TO_HOOKS_MIGRATION_OPUS.md with:

1) Current-State Control Surfaces
- What MCP is currently responsible for (by evidence)
- What hooks/scripts/compose already do (by evidence)
EVIDENCE per bullet.

2) Migration Candidates Table
Surface | Current mechanism | Proposed mechanism | Preconditions | Risks | Evidence
Only include candidates supported by evidence.

3) "Portability First" Plan (staged)
Stage 0: Observability + proof pack hardening
Stage 1: Low-risk moves (no behavior change)
Stage 2: Behavioral moves behind flags
Stage 3: Decommission candidates
Each stage must include:
- Entry criteria
- Steps
- Rollback
- Evidence links
- Risks mapped to R8

4) No-Go Triggers
List conditions that should stop migration, with evidence.

5) Minimal verification commands (suggestions only)
No claims of having run them.
