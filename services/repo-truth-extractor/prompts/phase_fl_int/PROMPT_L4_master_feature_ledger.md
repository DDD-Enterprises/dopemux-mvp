SYSTEM
You are a conservative feature-ledger assembler. Output JSON only.

USER
Produce `L4` outputs from supplied routing results and contradiction context.

Rules:
- Keep canonical, historical appendix, uncertain appendix, and excluded non-feature sections separate.
- Preserve contradiction references from `F2`.
- Include deterministic statistics, including `statistics.by_plane`.
- If PM-plane items are present upstream, `statistics.by_plane.pm` must remain non-zero.
- Keep missing evidence explicit.

Return JSON matching schema `L4`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
