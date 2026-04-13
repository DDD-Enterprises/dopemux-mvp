SYSTEM
You are a contract coverage auditor. Output JSON only.

USER
Assess Trinity, plane, tool, and proof-contract coverage using only supplied evidence.

Rules:
- Fail closed on missing evidence.
- Do not claim coverage where evidence is absent.
- Sort contracts deterministically by contract_id.

Return JSON matching schema S18.

S_INT_INPUT:
{{S_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
