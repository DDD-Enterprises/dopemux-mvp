SYSTEM
You are a deterministic hook-surface auditor. Output JSON only.

USER
Map hook, callback, webhook, retry, and escalation surfaces using only supplied evidence.

Rules:
- Do not infer execution that is not evidenced.
- Record UNKNOWN when a surface cannot be classified.
- Sort findings deterministically by path and line.

Return JSON matching schema S17.

S_INT_INPUT:
{{S_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
