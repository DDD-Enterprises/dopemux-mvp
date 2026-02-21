# PROMPT_E9 — Execution merge + normalize + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge all EXEC_* outputs, report coverage and suspicious gaps.

OUTPUTS:
  • EXEC_MERGED.json
  • EXEC_QA.json (counts_by_filekind, partitions_covered, missing_expected_outputs[], suspicious_empty[])

RULES:
  • Normalize arrays by stable sort, remove duplicate rows.
  • Preserve exact field names from upstream prompts.
