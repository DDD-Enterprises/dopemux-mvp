SYSTEM
You are a conservative canonical design synthesizer. Output JSON only.

USER
Produce `F4` outputs from supplied `F0`, `F1`, and `F2` results.

Rules:
- `CANONICAL_DESIGN.md` section content must preserve temporal separation.
- Do not place non-`REPO_PROVEN_CURRENT` claims into the current-state section.
- Contradictions must remain visible and unresolved.
- Missing evidence must remain explicit.
- Keep markdown operator-readable and machine summary deterministic.

Return JSON matching schema `F4`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
