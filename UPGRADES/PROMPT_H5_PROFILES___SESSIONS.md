# PROMPT_H5 — HOME profiles + sessions surfaces (SAFE MODE)

ROLE: Forensic extractor.
GOAL:
Extract home profiles (dopemux profiles, router profiles, model presets), plus session state files that influence behavior.

HARD RULES:
- Do not dump chat logs.
- Do not dump large session contents.
- Only list: file paths, profile names, toggles, and relevant keys.

OUTPUT: HOME_PROFILES_SURFACE.json
{
  "artifact": "HOME_PROFILES_SURFACE",
  "generated_at": "<iso8601>",
  "profiles": [
    {
      "path": "<absolute>",
      "profile_name": "<name>",
      "kind": "dopemux|router|taskx|other",
      "settings_keys": ["<keys only>"],
      "models": ["<literal model strings>"],
      "notes": "<short>"
    }
  ],
  "sessions": [
    {
      "path": "<absolute>",
      "kind": "cache|state|history|unknown",
      "signals": ["affects_routing","affects_tools","affects_tmux","unknown"],
      "notes": "<short>"
    }
  ]
}
