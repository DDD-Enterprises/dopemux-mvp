# PROMPT_H1_KEYS___REFERENCES
Goal: extract keys + cross-file references for home control plane (SAFE MODE)
Model: Gemini Flash (preferred)

## Mission
From the Phase H partitions (esp. H_P1..H_P4), extract:
- config keys (top-level + important nested)
- references between files (include/import/extends/include_path)
- referenced directories or db files
- referenced env var NAMES (values redacted)

Produce:
1) HOME_KEY_INDEX.json
2) HOME_REFERENCE_GRAPH.json
3) HOME_ENV_VAR_INDEX.json

## Rules
- Evidence for every key/ref:
  HOMECTRL: <path>#Lx-Ly  OR HOMECTRL: <path>:<unique_excerpt<=12_words>
- No inference. No values unless they are safe literals (e.g., booleans, small enums).
- If values are secrets or URLs with tokens: store "[REDACTED]" and cite.
- Deterministic ordering: sort keys and refs.

## Output 1: HOME_KEY_INDEX.json
{
  "artifact": "HOME_KEY_INDEX",
  "generated_at": "<iso8601>",
  "files": [
    {
      "path": "<file>",
      "format": "json|yaml|toml|ini|other",
      "keys": [
        {
          "key_path": "router.providers.openai.model",
          "value_hint": "string|int|bool|list|object|UNKNOWN",
          "value_literal_if_safe": "<literal_or_null>",
          "evidence": ["HOMECTRL: ..."]
        }
      ]
    }
  ]
}

## Output 2: HOME_REFERENCE_GRAPH.json
{
  "artifact": "HOME_REFERENCE_GRAPH",
  "generated_at": "<iso8601>",
  "edges": [
    {
      "from": "<file>",
      "to": "<file_or_dir_or_db>",
      "ref_type": "include|import|extends|path_ref|db_ref|url_ref|unknown",
      "evidence": ["HOMECTRL: ..."]
    }
  ],
  "orphans": [
    {"path": "<file>", "reason": "no outgoing refs observed"}
  ]
}

## Output 3: HOME_ENV_VAR_INDEX.json
{
  "artifact": "HOME_ENV_VAR_INDEX",
  "generated_at": "<iso8601>",
  "env_vars": [
    {
      "name": "OPENAI_API_KEY",
      "referenced_in": ["<file>"],
      "usage_hint": "auth|endpoint|db|logging|unknown",
      "risk": "HIGH|MED|LOW",
      "evidence": ["HOMECTRL: ..."]
    }
  ]
}

## Finish
Emit ONLY the three JSON artifacts.
No prose.
No markdown fences.
