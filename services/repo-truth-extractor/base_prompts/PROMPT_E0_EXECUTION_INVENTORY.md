# PROMPT E0 — Execution & Environment Inventory

## Goal
Scan the **{{ repo.name }}** repository for all execution-related artifacts: bootstrap commands, environment loading chains, service startup graphs, and runtime modes.

## Inputs
Scan the following:

{% for scope in scopes.get('E0', ['Makefile', 'Taskfile.*', 'package.json', 'pyproject.toml', 'compose*.yml', 'docker-compose*.yml', 'Dockerfile*', 'scripts/**/*.sh', '.env*', 'config/**/*']) %}
- `{{ scope }}`
{% endfor %}

{% if features.get('docker_compose', {}).get('present') %}
Analyze Docker Compose service definitions for startup ordering and dependencies.
{% endif %}
{% if features.get('dockerfile', {}).get('present') %}
Analyze Dockerfiles for build stages and entry points.
{% endif %}

## Outputs
- `EXECUTION_INVENTORY.json`

## Schema
```json
{
  "bootstrap_commands": [
    {
      "id": "string",
      "command": "string",
      "source_file": "string (repo-relative)",
      "description": "string",
      "evidence": [{ "path": "string", "line_range": [1, 5], "excerpt": "string ≤200 chars" }]
    }
  ],
  "env_files": [
    {
      "id": "string",
      "path": "string",
      "variables_count": "integer",
      "has_defaults": "boolean"
    }
  ],
  "services": [
    {
      "id": "string",
      "name": "string",
      "type": "string (docker|process|systemd|other)",
      "port": "integer|null",
      "depends_on": ["string"],
      "health_check": "string|null"
    }
  ]
}
```

## Extraction Procedure
1. Parse Makefile/Taskfile targets for bootstrap commands.
2. Scan `package.json` scripts and `pyproject.toml` scripts.
3. Parse Docker Compose for service definitions and dependency graphs.
4. Scan `.env*` files for variable counts.
5. Identify startup ordering from depends_on chains.
6. Emit execution inventory.

## Evidence Rules
- Every bootstrap command must cite its source file and line.
- `path` must be repo-relative.
- `excerpt` verbatim, ≤200 chars.

## Determinism Rules
- Sort by `id`.
- Stable IDs from content hash.
- No timestamps.

## Anti-Fabrication Rules
- Only report commands actually defined in config files.
- Do not infer undocumented scripts.
- If a service port is not explicitly configured, use `null`.

## Failure Modes
- If no execution artifacts found: emit empty arrays.
- If compose file has syntax errors: report but continue.
