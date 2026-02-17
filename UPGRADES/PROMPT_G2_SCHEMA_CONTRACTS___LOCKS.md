# PROMPT_G2 — Instruction authority hierarchy + conflict policy

ROLE: Governance extractor.
GOAL: Extract instruction hierarchy rules and conflict resolution policies stated in docs or configs.

OUTPUTS:
  • INSTRUCTION_AUTHORITY_POLICY.json
    - rules[]: {rule, applies_to, evidence_refs[]}
  • SUPERSESSION_POLICY_SURFACE.json
    - policies[]: {doc_or_rule, precedence, evidence_refs[]}

RULES:
  • No invention. If hierarchy isn’t stated, output empty arrays and annotate UNKNOWN.
