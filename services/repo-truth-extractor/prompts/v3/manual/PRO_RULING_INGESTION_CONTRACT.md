# PRO_RULING_INGESTION_CONTRACT

ROLE: Manual ruling ingestion contract for synthesis phases.
MODE: Deterministic, evidence-bounded, manual execution only.

PURPOSE:
- Define where manual PRO rulings are stored.
- Define required keys and sorting rules.
- Define how S-phase synthesis can consume these rulings.

MANUAL RULING FILE LOCATIONS:
- <run_dir>/manual_rulings/PRO_CONFLICT_RULING.<conflict_id>.json
- <run_dir>/manual_rulings/PRO_COLLISION_POLICY.<artifact_name>.json
- <run_dir>/manual_rulings/PRO_RISK_RERANK.<batch_id>.json

REQUIRED KEYS BY FILE:
1) PRO_CONFLICT_RULING
- conflict_id
- decision
- winner
- rationale_bullets
- missing_evidence

2) PRO_COLLISION_POLICY
- artifact_name
- policy
- canonical_key
- dedup_rule
- acceptance_tests

3) PRO_RISK_RERANK
- rerank
- notes

SORTING RULES:
- Sort file processing by path (lexicographic).
- For arrays:
  - rationale_bullets sorted by bullet where possible.
  - acceptance_tests sorted by test.
  - rerank sorted by risk_id.
- Do not include timestamps in normative synthesized outputs.

S-PHASE CONSUMPTION RULES:
- Phase S may ingest manual_rulings/PRO_*.json as optional inputs.
- If rulings exist:
  - S4_TRUTH_PACK_INDEX.json should include them in truth_pack_inputs.
  - S5_DECISION_GRAPH.json should emit edges referencing ruling decisions where evidence anchors exist.
- If rulings are absent, Phase S continues without failure.

EXECUTION RULE:
- This contract does not authorize automatic PRO prompt execution.
- Manual PRO prompts are run by operator decision only.
