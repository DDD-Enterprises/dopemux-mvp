# PROMPT_G1 — CI gates + enforcement truth

ROLE: Governance extractor.
GOAL: Extract enforced CI gates and where they run (CI, local, or both).

OUTPUTS:
  • CI_GATES_TRUTH.json
    - gates[]: {name, where(ci/local/both), command_literal, required, failure_behavior, evidence_refs[]}

RULES:
  • required must be UNKNOWN unless explicitly described as required.
 EOF