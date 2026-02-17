# PROMPT_E5 — Artifact outputs, logs, and state

ROLE: Execution plane extractor.
GOAL: map where runtime artifacts land (logs, sqlite DBs, caches, run dirs, out/ folders).

OUTPUTS:
  • EXEC_ARTIFACT_SURFACE.json (artifacts[]: {path, type(log/db/cache/report), writer, reader, retention_hint})

RULES:
  • Only include artifact locations explicitly mentioned in config/scripts/docs.
