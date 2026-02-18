# PROMPT_Q0 — Pipeline proof inventory (evidence pack)

ROLE: QA/doctor.
GOAL: Verify structure of phase outputs and produce an audit-friendly proof index for the current run.

INPUTS:
  • run directory structure and all phase manifests/norm merges for the current run_id

OUTPUTS:
  • PIPELINE_PROOF_INDEX.json
    - phases[]: {phase, has_raw, has_norm, has_qa, artifact_counts, missing_expected[], notes}
  • PIPELINE_PROOF_CHECKLIST.json
    - checks[]: {check_id, description, passed, evidence_refs[]}

RULES:
  • Structural QA only; do not assess semantic correctness of artifacts.
