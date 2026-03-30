# PROMPT_E4

## Goal
Produce `E4` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
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
- `EXEC_ENV_CHAIN.json`
- `EXEC_STARTUP_GRAPH.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_RUNTIME_MODES.json`
- `EXEC_MODE_DELTA_REPORT.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_RUNTIME_MODES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E4`
    - `id_rule`: `EXEC_RUNTIME_MODES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `EXEC_MODE_DELTA_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E4`
    - `id_rule`: `EXEC_MODE_DELTA_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**: Load `EXECUTION_INVENTORY.json`. Focus on configuration loaders, CLI entrypoints, and feature toggle files.
2.  **Identify Mode Triggers**:
    *   Scan for environment variables that switch modes: `APP_ENV`, `NODE_ENV`, `STAGE`, `DEBUG`.
    *   Scan for CLI flags: `--dev`, `--prod`, `--test`, `--dry-run`.
3.  **Map Mode-Specific Behavior**:
    *   Identify conditional logic in code: `if settings.is_dev:`, `if os.environ.get("DEBUG") == "1":`.
    *   Extract differences in: logging levels, database connection strings, security enforcements, and available API endpoints.
4.  **Detect Feature Toggles**:
    *   Scan for toggle definitions: `features.json`, `unleash` configs, or hardcoded boolean flags.
5.  **Build Mode Items**: For each identified mode, record:
    *   `mode_name`: e.g., "production", "development", "maintenance".
    *   `trigger_condition`: The literal env var or flag that activates it.
    *   `affected_behavior`: A concise description of what changes in this mode.
6.  **Evidence Anchoring**: Attach exact excerpts showing the conditional checks and mode definitions.
7.  **Validate**: Apply stable sorting by mode name. Emit `RUNTIME_MODES_DELTA.json`.
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
# PROMPT_E4 — RUNTIME MODES / DELTA REPORT

TASK: Identify runtime “modes” (dev/prod/smoke/local) + deltas.

OUTPUTS:
	•	EXEC_RUNTIME_MODES.json
	•	EXEC_MODE_DELTA_REPORT.json
```
