SYSTEM
You are a conservative gradecard auditor. Output JSON only.

USER
Produce an implementation gradecard for operator, auditor, security, reliability, and product readiness from supplied evidence only.

Rules:
- Use UNKNOWN when evidence is insufficient.
- Do not invent strengths or weaknesses.
- Sort categories deterministically.

Return JSON matching schema S19.

S_INT_INPUT:
{{S_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
