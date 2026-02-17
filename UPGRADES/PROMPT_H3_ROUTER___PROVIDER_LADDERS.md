# Phase H3: Home Router + Provider Ladder Hints

Goal:
- Extract any router configuration, model/provider selection ladders, fallback chains, or policy-like directives found in home control plane configs.

Outputs:
- HOME_ROUTER_SURFACE.json
- HOME_PROVIDER_LADDER_HINTS.json

HOME_ROUTER_SURFACE.json:
{
  "surface_version": "H3.v1",
  "generated_at": "<iso8601>",
  "router_configs": [
    {
      "path": "<path>",
      "router_type_hint": "<string>",
      "model_selection_rules": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}

HOME_PROVIDER_LADDER_HINTS.json:
{
  "hints_version": "H3.v1",
  "generated_at": "<iso8601>",
  "ladders": [
    {
      "name": "<string>",
      "providers_or_models": ["<string>"],
      "evidence": {"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "confidence": "<high|medium|low|hint_only>"
    }
  ]
}
