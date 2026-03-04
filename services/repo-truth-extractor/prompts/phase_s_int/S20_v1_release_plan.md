SYSTEM
You are a conservative release planner. Output JSON only.

USER
Produce a v1 release definition and milestone plan from supplied evidence only.

Rules:
- Do not invent completed work.
- Missing evidence must remain UNKNOWN.
- Sort milestones deterministically by milestone_id.

Return JSON matching schema S20.

S_INT_INPUT:
{{S_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
