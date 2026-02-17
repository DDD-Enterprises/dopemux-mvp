# Phase H1: Home Keys + References Surface (Safe)

Goal:
- Extract references to environment variables, API keys, token paths, credential file paths, and configuration include-chains that appear in the provided home control-plane files.
- Do NOT output secrets. Only output key NAMES, referenced FILE PATHS, and reference locations.

Hard rules:
- Never print actual secret values.
- Prefer explicit evidence: show (path, line_range, snippet_redacted) for each reference.
- Output valid JSON only.

Outputs:
- HOME_KEYS_SURFACE.json
- HOME_REFERENCES.json

HOME_KEYS_SURFACE.json:
{
  "surface_version": "H1.v1",
  "generated_at": "<iso8601>",
  "env_vars_referenced": [
    {
      "name": "<ENV_VAR_NAME>",
      "refs": [{"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}]
    }
  ],
  "credential_paths_referenced": [
    {
      "path": "<string>",
      "refs": [{"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}]
    }
  ],
  "notes": []
}

HOME_REFERENCES.json:
{
  "refs_version": "H1.v1",
  "generated_at": "<iso8601>",
  "includes_and_imports": [
    {
      "source_path": "<path>",
      "kind": "<include|import|source|extends|loads>",
      "target": "<string>",
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ]
}
