# PROMPT: A8 - Repo TaskX Surface

Phase: A
Step: A8

Outputs:
- REPO_TASKX_SURFACE.json

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
  "artifact": "REPO_TASKX_SURFACE.json",
  "phase": "A",
  "step": "A8",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "taskx:<stable_id>",
      "invocation": "...",
      "config_file": "...",
      "packet_path": "...",
      "operator_surface": "...",
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
- .taskx files, taskx config, scripts/workflows invoking taskx
- Packet paths, instruction compilation/injection surfaces, operator profile surfaces
