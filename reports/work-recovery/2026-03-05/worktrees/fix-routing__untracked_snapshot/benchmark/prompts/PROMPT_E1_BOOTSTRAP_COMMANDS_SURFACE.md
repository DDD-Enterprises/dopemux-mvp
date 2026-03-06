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
1. Load upstream `EXEC_INVENTORY.json` and `EXEC_PARTITIONS.json`; use the bootstrap/setup partition as primary scan surface.
2. Extract make targets and their recipes: parse Makefile(s) for all target names, prerequisites, and recipe commands; record exact invocation strings with file:line evidence.
3. Extract npm/yarn scripts from `package.json` `scripts` section; record script name and command string.
4. Extract pyproject.toml scripts from `[tool.poetry.scripts]` or `[project.scripts]` sections; record entrypoint names and module paths.
5. Scan shell scripts for canonical bootstrap commands: identify `docker compose up`, `make` invocations, `pip install`, `uv sync`, and service startup sequences; record the exact command string and calling context.
6. For each EXEC_BOOTSTRAP_COMMANDS item, populate `id`, required fields, and `evidence`.
7. Legacy Context is intent guidance only and is never evidence.
8. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
9. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
10. Attach evidence to every non-derived field and every relationship edge.
11. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
13. Emit exactly the declared outputs and no additional files.

## Evidence Rules
- Every load-bearing value must carry at least one evidence object:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- `path` must be repo-relative (never absolute in norm artifacts).
- `excerpt` must be exact (no paraphrase) and <= 200 chars.
- If the source is ambiguous, include multiple evidence objects and set value to `UNKNOWN`.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent endpoints, handlers, dependencies, env vars, commands, or policy claims.
- Do not infer intent from filenames alone; require direct textual/code evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Parameterized command: if a bootstrap command uses shell variables or arguments that change its behavior, emit with `value: parameterized` and evidence of the variable usage.
- Circular make dependency: if make targets form a dependency cycle, emit with `status: circular_dependency` and evidence of the cycle.

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
