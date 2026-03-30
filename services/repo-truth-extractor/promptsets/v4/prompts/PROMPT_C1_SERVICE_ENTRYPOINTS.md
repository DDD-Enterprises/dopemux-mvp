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
    - `required_item_fields`: `id, service_id, type, value, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

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
