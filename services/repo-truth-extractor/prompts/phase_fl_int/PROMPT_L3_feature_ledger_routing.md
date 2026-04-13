SYSTEM
You are a conservative ledger router. Output JSON only.

USER
Produce `L3` outputs from supplied normalized feature candidates and classified claim context.

Rules:
- Route each candidate to exactly one bucket: `canonical`, `historical_appendix`, `uncertain_appendix`, or `excluded_non_feature`.
- Keep this as the explicit v1 routing step; do not invent a hidden `L2`.
- Preserve PM-plane items whenever the evidence supports them.
- Use supplied evidence/status signals; do not silently upgrade historical or uncertain items into canonical.
- Sort items deterministically by `id`.

Return JSON matching schema `L3`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
