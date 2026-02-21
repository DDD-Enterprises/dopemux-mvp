# Phase S: Synthesis

## S: Synthesis (Architectural Vision)

Output files
	•	ARCHITECTURAL_SYNTHESIS.md
	•	MIGRATION_PLAN.md
	•	NEW_DATAFLOW_SHAPE.md

ROLE: Chief Architect. Synthesis / Reasoning. Markdown only.

TARGET: Arbitration Outputs (R) + Current codebase state (C) + Repo Control Plane (A) + Home Control Plane (H).

OBJECTIVE: Synthesize a unified architectural vision and migration plan.

OUTPUT 1: ARCHITECTURAL_SYNTHESIS.md
- High-level system architecture based on actual truth (R).
- Define clear subsystem boundaries and responsibilities.
- Identify architectural debt and structural flaws.

OUTPUT 2: MIGRATION_PLAN.md
- Concrete steps to move from current state (as arbitrated in R) to target architecture.
- Prioritized tasks (P0, P1, P2).
- Risk mitigation strategies.

OUTPUT 3: NEW_DATAFLOW_SHAPE.md
- Proposed dataflow for critical paths (e.g., memory capture, task execution).
- Diagrammatic representation (Mermaid or ASCII).

RULES:
- Synthesize, do not excavate. Use the evidence provided in previous phases.
- Be actionable. Avoid vague recommendations.
- Focus on stability, portability, and maintainability.
