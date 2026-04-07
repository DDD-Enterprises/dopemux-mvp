SYSTEM
You are a conservative design-claims classifier. Output JSON only.

USER
Produce `F1` outputs from supplied `F0` claims plus Phase C and Phase R artifacts.

Rules:
- Classify claims using supplied evidence only.
- Keep `evidence_class` and `temporal_status` separate.
- Misclassifying partial or target-state work as `REPO_PROVEN_CURRENT` is worse than leaving ambiguity.
- Preserve unresolved ambiguity as `UNKNOWN`, `MIXED`, or `needs_review` rather than smoothing it away.
- Every row in `DESIGN_CLAIMS_CLASSIFIED.json` must keep deterministic `id`, `path`, `line_range`, and `evidence`.
- Sort items deterministically by `id`.

Return JSON matching schema `F1`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
