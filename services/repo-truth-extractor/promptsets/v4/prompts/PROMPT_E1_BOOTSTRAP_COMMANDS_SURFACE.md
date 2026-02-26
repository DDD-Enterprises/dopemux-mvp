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
1. Parse `Makefile` and `*.mk` files to extract all Make targets: target name, recipe commands (exact strings), and dependencies (prerequisite targets). Record each target with file path and line range evidence.
2. Parse `package.json` `scripts` section to extract all npm script names and their command strings. Record each with file path and line range evidence.
3. Scan `pyproject.toml` and `setup.py`/`setup.cfg` for Python CLI entrypoints (`[project.scripts]`, `console_scripts`), and extract the module:function mapping. Record with evidence.
4. Extract compose service commands: parse `compose.yml` and `docker-compose*.yml` for `command`, `entrypoint`, and `build` directives. Record the exact command string per service with evidence.
5. Identify tmux/orchestrator wrapper scripts that invoke multiple services: scan `scripts/` for scripts containing `tmux`, `tmuxinator`, or equivalent session management commands. Extract the services/commands launched per pane/window.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

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
- Make recipe uses shell variable expansion or conditional logic that prevents static extraction of the command string: emit with `command: UNKNOWN` and `status: dynamic_recipe` with evidence.
- npm script delegates to another script via `npm run <other>`: emit both the delegating script and the chain, with `delegation_target` field linking them.

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
