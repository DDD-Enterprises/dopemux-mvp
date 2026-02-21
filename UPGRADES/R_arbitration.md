# Phase R: Arbitration

## R: Arbitration (Truth maps + conflict ledger)

Output files
	•	CONTROL_PLANE_TRUTH_MAP.md
	•	WORKFLOW_TRUTH_GRAPH.md
	•	TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
	•	DOPE_MEMORY_IMPLEMENTATION_TRUTH.md
	•	EVENTBUS_WIRING_TRUTH.md
	•	TASKX_INTEGRATION_TRUTH.md
	•	PORTABILITY_RISK_LEDGER.md

ROLE: Truth Arbitrator / System Auditor. Reasoning + Markdown only.

TARGET: All collected surfaces.
- HOME_* JSONs (H1–H4)
- A_REPO_CONTROL_PLANE.json (A)
- MERGED_DOCS.json (D)
- CODE_SURFACES.json (C)

OBJECTIVE: Resolve conflicts between documented architecture and actual implementation/configuration.

OUTPUT 1: CONTROL_PLANE_TRUTH_MAP.md
- Identify mismatches between repo config (A) and home config (H).
- Highlight overrides that break portability.
- Recommend synchronization strategy.

OUTPUT 2: WORKFLOW_TRUTH_GRAPH.md
- Map actual workflows found in code/hooks vs documented workflows.
- Identify zombie workflows (documented but not implemented) or ghost workflows (implemented but not documented).

OUTPUT 3: DOPE_MEMORY_IMPLEMENTATION_TRUTH.md
- Audit Chronicle/Capture implementation against Dope-Memory spec.
- Identify missing memory lanes or incorrect event types.

OUTPUT 4: PORTABILITY_RISK_LEDGER.md
- List all local-only dependencies or hardcoded paths found in (H) or (C).
- Risk score (High/Med/Low).

RULES:
- Be ruthless about truth. Code is truth, but config overrides code.
- Cite specific files/lines for every claim.
- Do not invent. If unknown, state "UNKNOWN".
