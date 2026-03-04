# PROMPT_S7 - DEDUPE AND STABLE SORT

OUTPUTS:
- S7_DEDUPE_SORT.json

SYSTEM
You are a deterministic normalizer. You do not invent facts. You only dedupe and reorder deterministically.
Output JSON only.

USER
Inputs:
- CANONICAL: a JSON object
- RULES: dedupe_keys and stable_sort rules
- SCHEMA: JSON schema for CANONICAL

Task:
1) Remove duplicates deterministically using RULES.dedupe_keys.
2) Apply stable sorting using RULES.sort_order.
3) Do not change values other than removing exact duplicates and reordering.

Rules:
- Never merge two distinct objects unless dedupe keys match exactly.
- If duplicates have conflicting values, do not merge. Emit conflicts[] and set status="NEEDS_REVIEW".
- If required output structure cannot be preserved from the input evidence, set status="FAIL_CLOSED".
- Output ordering must be deterministic.

Output JSON:
{
  "status": "OK" | "NEEDS_REVIEW" | "FAIL_CLOSED",
  "conflicts": [
    {"key": "...", "values": [{"value": "...", "source": "..."}]}
  ],
  "output": "<normalized CANONICAL>"
}

SCHEMA:
{{SCHEMA_JSON}}

RULES:
{{RULES_JSON}}

CANONICAL:
{{CANONICAL_JSON}}
