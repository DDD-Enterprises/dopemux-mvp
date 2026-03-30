# PROMPT_E1

## Goal
Produce `E1` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_BOOTSTRAP_COMMANDS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_BOOTSTRAP_COMMANDS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E1`
    - `id_rule`: `EXEC_BOOTSTRAP_COMMANDS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**: Load `EXECUTION_INVENTORY.json` and `EXECUTION_PARTITIONS.json`. Target scripts (`*.sh`, `*.ps1`), `Makefile`, `Dockerfile`, and `setup.py`/`pyproject.toml`.
2.  **Extract Install & Init Commands**:
    *   In `Makefile`: Identify targets like `install`, `setup`, `init`, `deps`, and `build`. Record the literal recipe lines.
    *   In `install.sh`/`bootstrap.sh`: Extract key command sequences (e.g., `pip install`, `npm install`, `apt-get`).
    *   In `Dockerfile`: Extract `RUN` commands specifically performing setup or dependency installation.
3.  **Map Command Metadata**: For each command, identify:
    *   `command_string`: The literal shell/executable string.
    *   `interpreter`: `bash`, `python`, `make`, etc.
    *   `is_idempotent`: Identify guards like `if [ ! -f ... ]` or `|| true`.
4.  **Populate Items**: Construct `BOOTSTRAP_COMMANDS` items with deterministic IDs based on `path|command_string`.
5.  **Evidence Anchoring**: Attach exact excerpts and line ranges for every command and guard identified.
6.  **Validate**: Apply deterministic sorting by path and line number. Emit `BOOTSTRAP_COMMANDS_SURFACE.json`.
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
# PROMPT_E1 — BOOTSTRAP COMMANDS SURFACE

TASK: Enumerate canonical “what starts what” commands.

MUST EXTRACT (literal strings):
	•	make targets and recipes
	•	npm scripts
	•	python entrypoints / CLI invocations
	•	compose up/down targets
	•	tmux wrappers invoked from repo side

OUTPUTS:
	•	EXEC_BOOTSTRAP_COMMANDS.json
```
