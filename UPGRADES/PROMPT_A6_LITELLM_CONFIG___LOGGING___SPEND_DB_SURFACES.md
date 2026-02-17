# PHASE A6 — LITELLM + LOGGING + SPEND DB SURFACES (REPO)
Model: Gemini Flash 3
Goal: Produce REPO_LITELLM_SURFACE.json

Hard rules:
- Only extract config and wiring points (not “how litellm works”).
- Evidence required for each surface.

Inputs:
- litellm.config*, litellm.config.yaml*, any docs/scripts referencing litellm, spend db, proxy, logging.

Task:
REPO_LITELLM_SURFACE.json must include:
- config_files[] (paths)
- proxy_endpoints[] (if literal URLs appear, redact host if needed; keep shape)
- logging_sinks[] (files/db/services)
- spend_db_surfaces[] (sqlite/postgres references, file paths, table names if literal)
- env_vars[] (names)
- invocation_points[] (scripts/commands that start proxy)
- evidence everywhere
