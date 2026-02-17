# PROMPT_H4 — HOME LiteLLM surface (SAFE MODE)

ROLE: Forensic extractor.
GOAL:
Extract home-level LiteLLM proxy configs, spend/log DB settings, routing, adapters.

HARD RULES:
- Redact API keys and headers.
- Keep only: file paths, config keys, model names, DB paths (paths ok), and ports (ok).

OUTPUT: HOME_LITELLM_SURFACE.json
{
  "artifact": "HOME_LITELLM_SURFACE",
  "generated_at": "<iso8601>",
  "configs": [
    {
      "path": "<absolute>",
      "proxy": { "host": "<string>", "port": "<int or string>", "mode": "<if present>" },
      "models": ["<literal model strings>"],
      "logging": { "db_paths": ["<paths>"], "keys": ["<key names>"] },
      "routing": { "keys": ["<key names>"], "notes": "<short>" },
      "env_keys": ["<keys only>"]
    }
  ]
}
