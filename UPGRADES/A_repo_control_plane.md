# Phase A: Repo Control Plane Scan

## A: Repo Control Plane Scan

Output files
	•	A_REPO_CONTROL_PLANE.json

ROLE: System Architect / Config Analyst. No code generation. JSON only.

TARGET: Repo working tree (current directory).

SCOPE:
- .github/workflows/*.yml
- docker-compose*.yml
- litellm.config.yaml
- mcp-proxy-config.yaml
- .pre-commit-config.yaml
- pyproject.toml
- package.json
- src/dopemux/cli.py (imports only)
- src/dopemux/config.py

OUTPUT: A_REPO_CONTROL_PLANE.json
Structure:
{
  "ci_pipelines": [
    { "name": "...", "path": "...", "triggers": [...] }
  ],
  "docker_services": [
    { "name": "...", "image": "...", "ports": [...] }
  ],
  "mcp_servers": [
    { "name": "...", "command": "...", "args": [...] }
  ],
  "litellm_config": {
    "models": [...],
    "providers": [...]
  },
  "hooks": [
    { "id": "...", "stages": [...] }
  ],
  "dependencies": {
    "python": [...],
    "node": [...]
  }
}

RULES:
- Extract configuration details only.
- Do not hallucinate.
- If a file is missing, omit the section or return empty list.
