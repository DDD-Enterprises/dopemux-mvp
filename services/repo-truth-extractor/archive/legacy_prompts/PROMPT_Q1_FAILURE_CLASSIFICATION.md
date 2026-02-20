# PROMPT_Q1 — Drift + coverage report (docs vs code vs control plane)

ROLE: QA/doctor.
GOAL: Surface drift signals without resolving them.

OUTPUTS:
  • DRIFT_SIGNALS.json
    - signals[]: {kind(doc_vs_code/doc_vs_ctrl/code_vs_ctrl), description, evidence_refs[]}
  • COVERAGE_GAPS.json
    - gaps[]: {area, missing_artifact_or_partition, why_it_matters, next_action_hint}

RULES:
  • No arbitration; signal with citations only.
