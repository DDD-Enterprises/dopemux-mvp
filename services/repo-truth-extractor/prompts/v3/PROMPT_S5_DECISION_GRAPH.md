# PROMPT_S5 - DECISION GRAPH

ROLE: Decision graph synthesist.
MODE: Evidence-bounded graph construction.

GOAL:
- Build a deterministic decision/risk/conflict/evidence graph from provided synthesis inputs.

OUTPUTS:
- S5_DECISION_GRAPH.json

HARD RULES:
1) Use only provided inputs.
2) No repository rescans.
3) No fabricated nodes, edges, IDs, or evidence anchors.
4) If an edge cannot be grounded, omit it and capture UNKNOWN in notes.

REQUIRED INPUTS:
- R7_CONFLICT_LEDGER.md
- R8_RISK_REGISTER_TOP20.md

OPTIONAL INPUTS:
- S0_ARCHITECTURE_SYNTHESIS_OPUS.md
- S1_MCP_TO_HOOKS_MIGRATION_PLAN.md
- S2_DECISION_DOSSIER.md
- S4_TRUTH_PACK_INDEX.json
- PRO_CONFLICT_RULING.<conflict_id>.json
- PRO_COLLISION_POLICY.<artifact_name>.json
- PRO_RISK_RERANK.<batch_id>.json

OUTPUT SCHEMA:
{
  "nodes": [
    {"id": "DEC-001", "type": "decision|risk|conflict|evidence", "label": "..."}
  ],
  "edges": [
    {"from": "DEC-001", "to": "RISK-014", "type": "mitigates|blocks|supported_by|references"}
  ],
  "notes": ["..."]
}

DETERMINISM:
- Use stable IDs only.
- Sort nodes by id.
- Sort edges by (from, to, type).
- Sort notes lexicographically when possible.
- Do not emit timestamps or runtime identity keys.
