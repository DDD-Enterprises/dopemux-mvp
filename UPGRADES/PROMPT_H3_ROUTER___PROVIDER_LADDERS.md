# PROMPT_H3 — HOME router/provider ladders (SAFE MODE)

ROLE: Forensic extractor.
GOAL:
Find home-level routing config, provider ladders, default models, fallbacks, cost/quality toggles.

HARD RULES:
- No values for keys/tokens. Redact.
- Only output models/providers if explicitly present (strings).

OUTPUTS:
A) HOME_ROUTER_SURFACE.json
{
  "artifact": "HOME_ROUTER_SURFACE",
  "generated_at": "<iso8601>",
  "router_files": [
    {
      "path": "<absolute>",
      "router_kind": "litellm|claude-code-router|dopemux-router|unknown",
      "providers": ["openai","anthropic","gemini","xai","other"],
      "models": ["<literal model strings>"],
      "routing_rules": ["<short redacted rules>"],
      "env_keys": ["<keys only>"]
    }
  ]
}

B) HOME_PROVIDER_LADDER_HINTS.json
{
  "artifact": "HOME_PROVIDER_LADDER_HINTS",
  "generated_at": "<iso8601>",
  "ladders": [
    {
      "name": "<ladder name>",
      "order": ["<provider/model strings in order>"],
      "conditions": ["cheap|fast|xhigh|fallback|offline|unknown"],
      "evidence": "<path/section>"
    }
  ]
}
