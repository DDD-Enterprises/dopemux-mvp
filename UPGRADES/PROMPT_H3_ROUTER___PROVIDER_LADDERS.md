# PROMPT_H3_ROUTER___PROVIDER_LADDERS
Goal: extract HOME router + provider ladder truth (SAFE MODE)
Model: Gemini Flash (preferred)

## Mission
From allowlisted home configs, extract the HOME routing reality:
- provider ladders / fallback chains
- model selection rules
- per-project or per-profile overrides
- any coupling to MCP servers, tools, or litellm proxies
- any mention of "hooks" or implicit triggers tied to routing

## Hard rules
- Evidence for each rule:
  HOMECTRL: <path>#Lx-Ly  OR HOMECTRL: <path>:<unique_excerpt<=12_words>
- Do not infer ladders; only extract where explicitly described.
- If routing is computed by code and not present in configs, mark UNKNOWN.

## Outputs (JSON only)
Produce:
1) HOME_ROUTER_SURFACE.json
2) HOME_PROVIDER_LADDER_HINTS.json
3) HOME_ROUTER_MCP_COUPLING.json

### 1) HOME_ROUTER_SURFACE.json
{
  "artifact": "HOME_ROUTER_SURFACE",
  "generated_at": "<iso8601>",
  "router_configs": [
    {
      "path": "<file>",
      "router_type": "dopemux|taskx|litellm|claude-code-router|unknown",
      "key_features": ["<literal_feature>"],
      "evidence": ["HOMECTRL: ..."]
    }
  ],
  "selection_rules": [
    {
      "rule_id": "HR1",
      "description": "<literal paraphrase constrained to what file says>",
      "providers": ["openai","anthropic","xai","google","unknown"],
      "models": ["<literal_model_id_or_UNKNOWN>"],
      "trigger": "<when_applies_literal_or_UNKNOWN>",
      "evidence": ["HOMECTRL: ..."]
    }
  ]
}

### 2) HOME_PROVIDER_LADDER_HINTS.json
{
  "artifact": "HOME_PROVIDER_LADDER_HINTS",
  "generated_at": "<iso8601>",
  "ladders": [
    {
      "ladder_id": "HL1",
      "scope": "global|profile|project|command|unknown",
      "order": [
        {"provider": "openai", "model": "gpt-5.2-extended", "evidence": ["HOMECTRL: ..."]},
        {"provider": "xai", "model": "grok-code-fast-1", "evidence": ["HOMECTRL: ..."]}
      ],
      "fallback_conditions": ["<literal_or_UNKNOWN>"],
      "evidence": ["HOMECTRL: ..."]
    }
  ],
  "unknowns": [
    {"area": "fallback_conditions", "reason": "Not explicit in configs", "evidence": ["HOMECTRL: ..."]}
  ]
}

### 3) HOME_ROUTER_MCP_COUPLING.json
{
  "artifact": "HOME_ROUTER_MCP_COUPLING",
  "generated_at": "<iso8601>",
  "couplings": [
    {
      "router": "<file_or_router_id>",
      "mcp_server": "<name_or_UNKNOWN>",
      "coupling_type": "tool_call|context_injection|filesystem|agent_spawn|unknown",
      "evidence": ["HOMECTRL: ..."]
    }
  ]
}

## Normalization
- Sort ladders by ladder_id.
- Sort rules by rule_id.
- Preserve provider order within ladders.

## Finish
Emit ONLY the three JSON artifacts.
No prose.
No markdown fences.
