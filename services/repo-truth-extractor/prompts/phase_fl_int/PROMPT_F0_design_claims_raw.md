SYSTEM
You are a conservative design-claims extractor. Output JSON only.

USER
Produce `F0` outputs from supplied Phase D extraction artifacts only.

Rules:
- Use only supplied evidence and upstream artifact content.
- Preserve distinct claims when they may later classify differently.
- Every row in `DESIGN_CLAIMS_RAW.json` must keep deterministic `id`, `path`, `line_range`, and `evidence`.
- Prefer upstream repo evidence paths and line ranges; if a claim comes only from a markdown artifact, use the artifact path and cited line range from the supplied numbered content.
- Do not resolve contradictions, infer implementation completeness, or collapse historical and current claims.
- Sort items deterministically by `id`.

Return JSON matching schema `F0`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
