# PROMPT_X2_FEATURE_TO_CODE_MAP

TASK: Build deterministic map from feature surface to code implementation loci.

OUTPUTS:
- FEATURE_CODE_MAP.json

REQUIREMENTS:
- For each feature, map to concrete modules/functions/scripts/services.
- Include coupling points to control-plane and runtime config where present.
- Retain unresolved mappings in unknowns with reasons.
