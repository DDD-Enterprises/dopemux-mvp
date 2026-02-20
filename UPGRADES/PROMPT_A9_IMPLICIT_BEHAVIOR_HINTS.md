# PROMPT: A9 - Repo Implicit Behavior Hints

Phase: A
Step: A9

Outputs:
- REPO_IMPLICIT_BEHAVIOR_HINTS.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_IMPLICIT_BEHAVIOR_HINTS.json",
  "phase": "A",
  "step": "A9",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "hint:<stable_id>",
      "hint_type": "...",
      "description": "...",
      "toggle_or_path": "...",
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- Explicitly documented implicit behavior: config search order, default paths, if-file-exists toggles, env-var toggles, hidden coupling points when directly stated
