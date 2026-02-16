Goal: REPO_COMPOSE_SERVICE_GRAPH.json

Prompt:
- Parse compose.yml + docker-compose*.yml + compose/**.
- Extract:
  - services, images/build contexts, volumes, env vars, depends_on, ports, profiles, networks.
- Output graph-ready JSON: nodes (services) + edges (depends_on/links) + env surfacing.