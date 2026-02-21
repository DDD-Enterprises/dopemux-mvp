# PROMPT: A7 - Repo LiteLLM Surface

Phase: A
Step: A7

Outputs:
- REPO_LITELLM_SURFACE.json

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
  "artifact": "REPO_LITELLM_SURFACE.json",
  "phase": "A",
  "step": "A7",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "litellm:<stable_id>",
      "config_file": "...",
      "provider": "...",
      "model": "...",
      "env_var_requirements": ["..."],
      "budgets": ["..."],
      "rate_limits": ["..."],
      "cache_settings": ["..."],
      "logging_or_db": ["..."],
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
- LiteLLM config files/references, model/provider declarations
- Expected env var names only, budgets/rate limits/cache/logging/db settings if present
