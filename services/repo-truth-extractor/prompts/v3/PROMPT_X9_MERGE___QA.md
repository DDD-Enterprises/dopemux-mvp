# PROMPT_X9_MERGE___QA

TASK: Merge Feature Index outputs and emit QA.

INPUTS:
- Raw/partition outputs from X0..X4.

OUTPUTS:
- FEATURE_INDEX_MERGED.json
- FEATURE_INDEX_QA.json

RULES:
- Deterministic merge only; no rescans.
- Deduplicate by stable feature identity keys.
- Report coverage, unresolved mappings, and schema/required-field checks.
