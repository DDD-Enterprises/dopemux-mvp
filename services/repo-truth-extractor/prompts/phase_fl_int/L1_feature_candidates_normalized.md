SYSTEM
You are a conservative feature normalizer. Output JSON only.

USER
Produce `L1` outputs from supplied raw feature candidates only.

Rules:
- Normalize naming conservatively.
- Under-merge is safer than over-merge.
- Never merge across different evidence classes unless the supplied evidence directly supports it.
- Preserve upstream evidence, temporal, and plane signals in normalized rows.
- `FEATURE_MERGE_LOG.json` must explain each merge deterministically.
- Sort all emitted items deterministically by `id`.

Return JSON matching schema `L1`.

FL_INT_INPUT:
{{FL_INT_INPUT_JSON}}

PRIOR_OUTPUTS:
{{PRIOR_OUTPUTS_JSON}}
