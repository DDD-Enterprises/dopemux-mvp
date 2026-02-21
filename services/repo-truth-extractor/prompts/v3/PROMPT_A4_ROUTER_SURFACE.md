# PROMPT: A4 - Repo Router Surface

Phase: A
Step: A4

Outputs:
- REPO_ROUTER_SURFACE.json

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
  "artifact": "REPO_ROUTER_SURFACE.json",
  "phase": "A",
  "step": "A4",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "route:<stable_id>",
      "provider": "...",
      "model": "...",
      "trigger": "...",
      "fallback_ladder": ["..."],
      "retry_policy": "...",
      "rate_limit_policy": "...",
      "profile": "...",
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
- Provider/model routing tables, fallback ladders, profiles, routing rules
- Any retry/backoff/rate-limit knobs if present
- Routing policy files if present
