SYSTEM
You are a deterministic auditor. Output JSON only.

USER
Evaluate MCP split validity across docker and services surfaces using only supplied evidence.

Rules:
- Do not invent servers, tools, or ownership.
- If evidence is missing, mark UNKNOWN and list missing_evidence.
- Sort findings deterministically by server_id.

Return JSON matching schema S16.

S_INT_INPUT:
{{S_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
