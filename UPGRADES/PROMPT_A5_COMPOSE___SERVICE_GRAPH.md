# PHASE A5 — COMPOSE SERVICE GRAPH (REPO)
Model: Gemini Flash 3
Goal: Produce REPO_COMPOSE_SERVICE_GRAPH.json

Hard rules:
- Graph must be mechanically derived from compose files only.
- Redact secrets: never output env var VALUES if they look like keys/tokens. Keep names.
- Evidence required for each service.

Inputs:
- compose.yml, docker-compose*.yml, compose/**, docker/** compose-related files.

Task:
Produce a graph-ready JSON:
- compose_files[] (paths)
- services[]:
  - service_name
  - image/build (literal)
  - depends_on[] (literal)
  - ports[] (literal)
  - volumes[] (literal)
  - env_vars[] (names only; values only if clearly non-secret)
  - profiles[] (literal)
  - networks[] (literal)
  - evidence {path, anchor_excerpt}
- edges[]:
  - from_service -> to_service
  - edge_type ("depends_on"|"links"|"shares_volume"|"network")
  - evidence

Output:
REPO_COMPOSE_SERVICE_GRAPH.json
