# Phase H4: Home LiteLLM Surface

Goal:
- Extract LiteLLM config references, proxy configs, spend/log DB hints, and provider entries from home control-plane.

Outputs:
- HOME_LITELLM_SURFACE.json

HOME_LITELLM_SURFACE.json:
{
  "surface_version": "H4.v1",
  "generated_at": "<iso8601>",
  "configs": [
    {
      "path": "<path>",
      "providers": ["<string>"],
      "models": ["<string>"],
      "db_or_logs": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}
