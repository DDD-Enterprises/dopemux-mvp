# PROMPT_C1

## Goal
Produce `C1` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Focus on service runtime truths, interfaces, dependencies, and code-level ownership.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`




- `docker/**`
- `compose.yml`
- `docker-compose*.yml`
- `services/registry.yaml`
- Upstream normalized artifacts available to this step:
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `SERVICE_ENTRYPOINTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `SERVICE_ENTRYPOINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C9`
    - `id_rule`: `SERVICE_ENTRYPOINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, service_id, entrypoint_type, invocation, module_path, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "SERVICE_ENTRYPOINTS:<hash>",
  "service_id": "<service name from registry.yaml or module path>",
  "entrypoint_type": "uvicorn|gunicorn|cli_click|cli_typer|cli_argparse|script_direct|docker_cmd|docker_entrypoint|console_script|makefile_target|compose_command",
  "invocation": "<exact command or symbol used to start, e.g. 'uvicorn app:app --port 8000'>",
  "module_path": "<Python module path, e.g. 'services.task_orchestrator.app:app'>",
  "port": "<integer port number, or null if not network-facing>",
  "bind_host": "<bind address, e.g. '0.0.0.0', '127.0.0.1', or null>",
  "startup_args": ["<CLI flags or env-controlled startup parameters>"],
  "health_check_path": "<HTTP health check endpoint path, or null>",
  "restart_policy": "always|on_failure|no|unless_stopped|null",
  "depends_on": ["<other service names this entrypoint depends on>"],
  "is_production": true,
  "path": "<repo-relative path to entrypoint definition>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Entrypoint Type Definitions
- **uvicorn**: ASGI server invocation via `uvicorn module:app` (directly or via Python `-m`)
- **gunicorn**: WSGI/ASGI server invocation via `gunicorn` with worker configuration
- **cli_click**: Click-based CLI entrypoint using `@click.command()` or `@click.group()`
- **cli_typer**: Typer-based CLI entrypoint using `typer.Typer()` app
- **cli_argparse**: Standard library `argparse.ArgumentParser` CLI entrypoint
- **script_direct**: Direct Python script execution (`python script.py` or `#!/usr/bin/env python`)
- **docker_cmd**: `CMD` instruction in Dockerfile defining container startup command
- **docker_entrypoint**: `ENTRYPOINT` instruction in Dockerfile
- **console_script**: Entry defined in `pyproject.toml` `[project.scripts]` or `setup.py` `console_scripts`
- **makefile_target**: Make target that starts a service (e.g., `make run`, `make serve`)
- **compose_command**: Docker Compose `command:` override in compose.yml

### Worked Example
```json
{
  "id": "SERVICE_ENTRYPOINTS:d5f3a9b2",
  "service_id": "task-orchestrator",
  "entrypoint_type": "uvicorn",
  "invocation": "uvicorn task_orchestrator.app:app --host 0.0.0.0 --port 8100",
  "module_path": "task_orchestrator.app:app",
  "port": 8100,
  "bind_host": "0.0.0.0",
  "startup_args": ["--host", "0.0.0.0", "--port", "8100"],
  "health_check_path": "/health",
  "restart_policy": "on_failure",
  "depends_on": ["redis", "postgres"],
  "is_production": true,
  "path": "services/task-orchestrator/Dockerfile",
  "line_range": [22, 22],
  "status": "ok",
  "evidence": [{"path": "services/task-orchestrator/Dockerfile", "line_range": [22, 22], "excerpt": "CMD [\"uvicorn\", \"task_orchestrator.app:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8100\"]"}]
}
```

## Extraction Procedure
1. Load upstream inventory and partitions; use the service entrypoint partition as primary scan surface.
2. Scan `src/**` and `services/**` for `if __name__ == "__main__":` blocks and `main()` functions to identify direct execution entrypoints.
3. Scan `compose.yml` and `docker-compose*.yml` for `command:` and `entrypoint:` fields to identify canonical service start strings and runtime parameters.
4. Search for FastAPI/Flask app definitions (e.g., `app = FastAPI()`, `app = Flask(__name__)`) and decorators like `@app.get`, `@app.post`, `@app.route` to map API entrypoints.
5. Identify CLI entrypoints in `pyproject.toml` (under `[project.scripts]`), `setup.py` (under `entry_points`), or `Makefile` targets.
6. Locate uvicorn, gunicorn, or celery invocation patterns in shell scripts (`*.sh`) and service definition files.
7. Build relationship graph: trace connections between extracted service entrypoint elements and their underlying module symbols.
8. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts between code-level entrypoints and orchestration-level commands.
9. For each SERVICE_ENTRYPOINTS item, populate `id`, required fields, and `evidence`.
10. Legacy Context is intent guidance only and is never evidence.
11. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
12. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
13. Attach evidence to every non-derived field and every relationship edge.
14. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
15. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
16. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: SERVICE_ENTRYPOINTS.json

Prompt:
- Find how services start:
  - main modules, cli entrypoints, compose commands, uvicorn/gunicorn, scripts.
- Extract exact invocation strings + module symbols.
```
