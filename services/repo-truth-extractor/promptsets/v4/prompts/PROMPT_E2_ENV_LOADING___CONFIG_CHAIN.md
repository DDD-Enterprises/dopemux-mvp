# PROMPT_E2

## Goal
Produce `E2` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `compose.yml`
- `docker-compose*.yml`
- `Makefile`
- `src/**`
- Upstream normalized artifacts available to this step:
- `EXEC_INVENTORY.json`
- `EXEC_PARTITIONS.json`
- `EXEC_BOOTSTRAP_COMMANDS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_ENV_CHAIN.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_ENV_CHAIN.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E2`
    - `id_rule`: `EXEC_ENV_CHAIN:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**: Load `EXECUTION_INVENTORY.json`. Focus on source code (`*.py`, `*.ts`), `.env.example`, and `config/*.yaml`.
2.  **Scan for Environment Access**:
    *   In Python: Identify `os.getenv`, `os.environ`, `dotenv.load_dotenv`, and Pydantic `BaseSettings`.
    *   In TypeScript/JS: Identify `process.env`.
    *   In Docker/Compose: Identify `environment:` and `env_file:` sections.
3.  **Identify Configuration Cascades**:
    *   Find functions like `load_config()`, `get_settings()`, or `init_app()`.
    *   Trace how variables are merged (e.g., CLI args > Env Vars > Default Config).
4.  **Extract Variable Metadata**: For each variable, record:
    *   `name`: The literal env var name.
    *   `default`: The hardcoded fallback value.
    *   `is_required`: Boolean based on `raise` if missing or Pydantic validation.
    *   `source`: File and line where it is first defined or accessed.
5.  **Evidence Anchoring**: Attach exact excerpts for every access point and default value.
6.  **Validate**: Deduplicate by variable name and file path. Emit `ENV_LOADING_CONFIG_CHAIN.json`.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_E2 — ENV LOADING / CONFIG CHAIN

TASK: Map env var sources and config precedence chain.

MUST EXTRACT:
	•	.env loading behavior and where it occurs
	•	config file resolution order
	•	env var names and their consumers (by reference only, no guessing)

OUTPUTS:
	•	EXEC_ENV_CHAIN.json
```
