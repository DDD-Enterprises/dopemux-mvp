# PROMPT_H7 — HOME sqlite/state DB metadata (SAFE MODE)

ROLE: Forensic extractor.
GOAL:
Identify sqlite DB files in allowlist roots and extract ONLY metadata signals.
No row dumps.

OUTPUT: HOME_SQLITE_SCHEMA.json
{
  "artifact": "HOME_SQLITE_SCHEMA",
  "generated_at": "<iso8601>",
  "dbs": [
    {
      "path": "<absolute>",
      "size": <int>,
      "mtime": <epoch_seconds>,
      "role_guess": "context|index|cache|spend|unknown",
      "schema_excerpt": "<if schema is present in nearby .md/.sql files, cite that instead of introspecting>"
    }
  ],
  "notes": [
    "If schema cannot be derived safely without opening DB: mark UNKNOWN and list what tool/step would be needed."
  ]
}
