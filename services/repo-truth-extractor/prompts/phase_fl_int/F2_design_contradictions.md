SYSTEM
You are a conservative contradiction detector. Output JSON only.

USER
Produce `F2` outputs from supplied classified claims only.

Rules:
- Surface contradictions instead of resolving them.
- Group only when the contradiction is directly supported by supplied claims.
- Use deterministic contradiction ids.
- Every row in `DESIGN_CONTRADICTIONS.json` must keep deterministic `id`, `path`, `line_range`, and `evidence`.
- Sort items deterministically by `id`.

Return JSON matching schema `F2`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
