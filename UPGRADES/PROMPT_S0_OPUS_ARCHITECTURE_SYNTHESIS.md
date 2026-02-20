# PROMPT_S0 — OPUS ARCHITECTURE + SUBSYSTEM SYNTHESIS (from Truth Pack)

ROLE: Opus Reviewer/Synthesist.
MODE: Evidence-bounded synthesis. No excavation.

GOAL:
Produce a coherent, decision-grade architecture map for Dopemux and how TaskX fits into it,
using ONLY the Truth Pack outputs from Phase R (+ supporting indices from X, and doc clusters from D).

HARD RULES:
1) Do NOT rescan repo. Do NOT infer undocumented mechanisms.
2) Every non-trivial claim MUST cite one of the Phase R truth artifacts, using:
   EVIDENCE: <filename>#<section or anchor>
3) If evidence is missing or ambiguous: write UNKNOWN and specify exactly what artifact is missing.
4) Prefer "implemented reality" over "planned intent":
   - IMPLEMENTED comes from Phase R's CODE-based sections
   - PLANNED comes from Phase R's DOC-based sections
5) No refactors. No rewriting. Only architecture decisions + bounded recommendations.

INPUTS (required):
- R0 CONTROL_PLANE_TRUTH_MAP.md
- R1 DOPE_MEMORY_IMPLEMENTATION_TRUTH.md
- R2 EVENTBUS_WIRING_TRUTH.md
- R3 TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
- R4 TASKX_INTEGRATION_TRUTH.md
- R5 WORKFLOWS_TRUTH_GRAPH.md
- R6 PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- R7 CONFLICT_LEDGER.md
- R8 RISK_REGISTER_TOP20.md
Optional but helpful:
- X feature index outputs (X* merged/norm)
- D doc clusters + supersession outputs

DELIVERABLE:
Write ARCHITECTURE_SYNTHESIS_OPUS.md with:

1) Executive Architecture Snapshot (1 page)
- What exists today (implemented)
- What is planned but not implemented
- Key boundaries and planes
EVIDENCE required per bullet.

2) Subsystem Boundary Map
For each subsystem:
- Purpose
- Inputs/outputs
- Persistence surfaces (db/files)
- Control plane dependencies
- Failure modes
EVIDENCE required.

Subsystems must include at minimum:
- Dope-Memory
- EventBus
- Trinity/Boundary enforcement
- TaskX integration surface
- Control plane (repo + home)
- Workflow runners + bootstrap (compose/tmux/scripts/mcp)

3) "Truth-First" Dataflow Diagrams (text diagrams)
- Control plane -> runtime entrypoints
- Event flow (producer -> bus -> consumer)
- Memory flow (ingest -> store -> replay)
All steps must cite.

4) Decision Points (bounded)
List decisions Opus recommends you make next:
- Each decision must include:
  - Evidence summary
  - Options (2-3)
  - Risks (tie to R8)
  - Minimal verification commands (suggestions only)

5) "Where Opus cannot decide"
Explicit UNKNOWN list with what would be needed to decide.
