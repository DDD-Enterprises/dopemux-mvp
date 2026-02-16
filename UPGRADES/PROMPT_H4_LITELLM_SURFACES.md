# PROMPT_H4_LITELLM_SURFACES
Goal: extract HOME LiteLLM surface + spend/logging/db hints (SAFE MODE)
Model: Gemini Flash (preferred)

## Mission
From allowlisted home roots ONLY:
- ~/.dopemux/litellm/** (if exists)
- ~/.config/litellm/**
- ~/.config/dopemux/** (only if it references litellm)
- ~/.dopemux/** (only if it references litellm)

Extract:
1) LiteLLM proxy config surfaces (endpoints, router rules, model maps)
2) Spend/logging db surfaces (sqlite paths, db filenames, schema hints if present in text)
3) Provider credential dependency surface (ENV VAR NAMES only)
4) Observability surfaces: log files, tracing flags, retention knobs, request/response logging toggles
5) Cross-links: how dopemux/taskx router references litellm (if explicit)

## Hard rules
- SAFE MODE: never output key values, tokens, auth headers, bearer strings.
- Evidence for every item:
  HOMECTRL: <path>#Lx-Ly  OR HOMECTRL: <path>:<unique_excerpt<=12_words>
- No inference: if not present, mark UNKNOWN.
- Prefer literal config keys and their safe literals (booleans, ints, enums).
- If you see any raw secrets, replace with "[REDACTED]" and cite.

## Output artifacts (JSON only)
Produce:
1) HOME_LITELLM_SURFACE.json
2) HOME_LITELLM_SPEND_DB_SURFACE.json
3) HOME_LITELLM_ENV_DEPS.json

### 1) HOME_LITELLM_SURFACE.json
{
  "artifact": "HOME_LITELLM_SURFACE",
  "generated_at": "<iso8601>",
  "configs": [
    {
      "path": "<file>",
      "format": "yaml|json|toml|env|other",
      "proxy": {
        "enabled": "<bool_or_UNKNOWN>",
        "host": "<literal_or_UNKNOWN>",
        "port": "<int_or_UNKNOWN>",
        "base_url": "<literal_or_UNKNOWN>",
        "evidence": ["HOMECTRL: ..."]
      },
      "routing": {
        "has_router_rules": "<bool_or_UNKNOWN>",
        "model_mappings": [
          {
            "alias": "<alias_or_UNKNOWN>",
            "target": "<model_id_or_UNKNOWN>",
            "provider": "<provider_or_UNKNOWN>",
            "evidence": ["HOMECTRL: ..."]
          }
        ],
        "fallbacks": [
          {
            "order": [{"provider":"...","model":"..."}],
            "condition": "<literal_or_UNKNOWN>",
            "evidence": ["HOMECTRL: ..."]
          }
        ]
      },
      "logging": {
        "request_logging": "<bool_or_UNKNOWN>",
        "response_logging": "<bool_or_UNKNOWN>",
        "log_destination": "<literal_or_UNKNOWN>",
        "evidence": ["HOMECTRL: ..."]
      }
    }
  ],
  "unknowns": [
    {"area": "model_mappings", "reason": "No mappings observed in scanned configs"}
  ]
}

### 2) HOME_LITELLM_SPEND_DB_SURFACE.json
{
  "artifact": "HOME_LITELLM_SPEND_DB_SURFACE",
  "generated_at": "<iso8601>",
  "datastores": [
    {
      "type": "sqlite|postgres|file|unknown",
      "path_or_dsn": "<literal_or_REDACTED_or_UNKNOWN>",
      "schema_hints": ["<literal_table_name_or_UNKNOWN>"],
      "evidence": ["HOMECTRL: ..."]
    }
  ],
  "retention": [
    {"knob": "<key_path>", "value_literal_if_safe": "<literal_or_null>", "evidence": ["HOMECTRL: ..."]}
  ]
}

### 3) HOME_LITELLM_ENV_DEPS.json
{
  "artifact": "HOME_LITELLM_ENV_DEPS",
  "generated_at": "<iso8601>",
  "env_vars": [
    {
      "name": "OPENAI_API_KEY",
      "usage_hint": "provider_auth|proxy_auth|db_auth|unknown",
      "risk": "HIGH|MED|LOW",
      "referenced_in": ["<file>"],
      "evidence": ["HOMECTRL: ..."]
    }
  ],
  "notes": ["Names only; values redacted by policy."]
}

## Determinism
- Sort configs by path.
- Sort mappings by alias.
- Preserve explicit ordering for fallback ladders.

## Finish
Emit ONLY the three JSON artifacts.
No prose.
No markdown fences.
