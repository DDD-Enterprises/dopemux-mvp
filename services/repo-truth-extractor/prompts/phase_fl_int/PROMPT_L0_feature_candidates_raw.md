SYSTEM
You are a conservative feature harvester. Output JSON only.

USER
Produce `L0` outputs from supplied Phase D, Phase C, optional Phase X, and classified-claim inputs.

Rules:
- Harvest candidate features only from supplied evidence.
- If Phase X is absent, continue using D/C/F1 evidence only.
- Keep PM-plane features; do not filter them out because they are governance or workflow oriented.
- Every row in `FEATURE_CANDIDATES_RAW.json` must keep deterministic `id`, `path`, `line_range`, and `evidence`.
- Sort items deterministically by `id`.

Return JSON matching schema `L0`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
