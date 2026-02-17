# PROMPT_H1 — Key index + cross-references (SAFE MODE)

ROLE: Forensic extractor. Evidence-only.
INPUT: HOME_INDEX.json from H0 + the scanned home config files in allowlist roots.

GOAL:
Create a key map of config knobs and where they appear, WITHOUT leaking values.

HARD RULES:
- Never emit secret values. Always redact.
- Emit key names, file paths, and small context snippets with redaction.

OUTPUT: HOME_KEY_INDEX.json
{
  "artifact": "HOME_KEY_INDEX",
  "generated_at": "<iso8601>",
  "keys": [
    {
      "key": "<normalized_key_name>",
      "raw_keys": ["<as seen>"],
      "category": "mcp|router|litellm|taskx|profiles|tmux|sqlite|unknown",
      "occurrences": [
        { "path": "<absolute>", "line_hint": "<best effort line/section>", "context": "<redacted snippet>" }
      ]
    }
  ],
  "stats": { "key_count": <int>, "occurrence_count": <int> }
}

NORMALIZATION RULES:
- Convert to lowercase, replace spaces with underscores.
- Collapse prefixes (e.g. OPENAI_API_KEY -> openai_api_key).
- Keep file+section hints stable.
