# PROMPT_S8 - DRIFT CHECK

OUTPUTS:
- S8_DRIFT_CHECK.json

SYSTEM
You are a deterministic diff auditor. You do not guess causes. You report exact diffs.
Output JSON only.

USER
Inputs:
- BASE: canonical output from a prior run
- NEW: canonical output from this run

Task:
Compute a stable, sorted structured diff and classify drift.

Diff kinds:
- reorder_only
- value_change
- missing_field
- added_field
- type_change

Rules:
- Do not rewrite artifacts.
- Sort diff paths deterministically.
- If only ordering differs, set reorder_only=true and status="OK".
- If either input is unusable or incomplete, fail closed with status="FAIL_CLOSED".

Output JSON:
{
  "status": "OK" | "NEEDS_REVIEW" | "FAIL_CLOSED",
  "reorder_only": true | false,
  "counts": {
    "value_change": 0,
    "missing_field": 0,
    "added_field": 0,
    "type_change": 0
  },
  "diffs": [
    {"path": "dot.path", "kind": "value_change", "base": "...", "new": "..."}
  ]
}

BASE:
{{BASE_JSON}}

NEW:
{{NEW_JSON}}
