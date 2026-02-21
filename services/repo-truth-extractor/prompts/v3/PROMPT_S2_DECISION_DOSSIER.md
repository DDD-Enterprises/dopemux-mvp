# PROMPT_S2 - DECISION DOSSIER (evidence-bounded)

ROLE: Decision synthesist.
MODE: Compression and arbitration-ready synthesis from trusted artifacts only.

GOAL:
- Convert synthesis findings into a decision dossier that can drive implementation packets.

OUTPUTS:
- S2_DECISION_DOSSIER.md

HARD RULES:
1) Use only supplied synthesis artifacts.
2) Every decision row must include evidence anchors.
3) If evidence is insufficient, output UNKNOWN and required evidence.
4) Keep entries deterministic, concise, and mechanically actionable.

INPUTS (required):
- S0_ARCHITECTURE_SYNTHESIS_OPUS.md
- S1_MCP_TO_HOOKS_MIGRATION_PLAN.md
- R7_CONFLICT_LEDGER.md
- R8_RISK_REGISTER_TOP20.md

INPUTS (optional):
- FEATURE_INDEX_MERGED.json
- TP_MERGED.json

OUTPUT FORMAT (write the full content of S2_DECISION_DOSSIER.md):
1) Decision Table
- decision_id
- context
- options
- recommendation
- evidence anchors
- risk_ids
- verification suggestions
- stop conditions

2) Escalation Queue
- Items requiring PRO rulings with conflict and risk references.

3) UNKNOWN Register
- Explicit unresolved decisions and missing evidence sources.
