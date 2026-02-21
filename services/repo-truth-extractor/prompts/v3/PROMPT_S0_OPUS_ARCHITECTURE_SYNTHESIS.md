# PROMPT_S0 - OPUS ARCHITECTURE + SUBSYSTEM SYNTHESIS (from Truth Pack)

ROLE: Synthesis writer (deep, evidence-bounded).
MODE: Evidence-bounded synthesis. No excavation.

GOAL:
- Produce a decision-grade architecture map for Dopemux using only phase synthesis inputs.
- Preserve implemented vs planned distinctions and fail closed on missing evidence.

OUTPUTS:
- S0_ARCHITECTURE_SYNTHESIS_OPUS.md

HARD RULES:
1) Do not rescan the repo or home. Use only supplied synthesis artifacts.
2) Every non-trivial claim must end with:
   EVIDENCE: <artifact_filename>#<section_heading_or_anchor>
3) If evidence is missing or ambiguous, write UNKNOWN and name the missing artifact(s).
4) Prefer IMPLEMENTED over PLANNED. Label both explicitly. If unclear, mark UNKNOWN.
5) Use deterministic language only. No hedging, no timestamps, no non-auditable claims.

INPUTS (required):
- R0_CONTROL_PLANE_TRUTH_MAP.md
- R1_DOPE_MEMORY_IMPLEMENTATION_TRUTH.md
- R2_EVENTBUS_WIRING_TRUTH.md
- R3_TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
- R4_TASKX_INTEGRATION_TRUTH.md
- R5_WORKFLOWS_TRUTH_GRAPH.md
- R6_PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- R7_CONFLICT_LEDGER.md
- R8_RISK_REGISTER_TOP20.md

INPUTS (optional):
- FEATURE_INDEX_MERGED.json
- TP_MERGED.json
- TP_SUMMARY.md
- FREEZE_MANIFEST.json
- FREEZE_README.md

OUTPUT FORMAT (write the full content of S0_ARCHITECTURE_SYNTHESIS_OPUS.md):
1) Architecture Snapshot
- Current implemented control planes, data planes, and operational boundaries.
- Planned or disputed surfaces clearly separated.

2) Subsystem Boundary Map
- control plane
- dope-memory
- eventbus
- trinity, boundaries, and guardrails
- taskx integration
- workflow and automation surfaces

3) Conflict Consumption (from R7)
- For each top conflict, classify as RESOLVED or ESCALATE_TO_PRO.
- Include decision rationale with evidence anchors for both sides.

4) Risk-to-Decision Mapping (from R8)
- Each major decision must cite at least one risk ID from R8.
- Include mitigation notes tied to cited risk evidence.

5) Decision Points
- 2-3 options per decision
- recommendation
- stop conditions
- minimal verification suggestions (commands are suggestions only)

6) UNKNOWN Register
- Strict list of unresolved claims and exact missing evidence artifacts.

7) PRO_ESCALATIONS
- Output a deterministic list sorted by escalation_id.
- Each row must include:
  - escalation_id
  - conflict_id
  - kind (conflict|collision|risk)
  - recommended_manual_prompt (MANUAL_PRO_CONFLICT_RULING.md|MANUAL_PRO_COLLISION_POLICY.md|MANUAL_PRO_RISK_RERANK.md)
  - missing_evidence[]
- If no escalations are needed, output an empty list.
