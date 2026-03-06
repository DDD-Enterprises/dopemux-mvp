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
1. Load upstream `EXEC_INVENTORY.json`, `EXEC_PARTITIONS.json`, `EXEC_BOOTSTRAP_COMMANDS.json`, and `EXEC_ENV_CHAIN.json`; use the env chain to identify mode-switching variables.
2. Identify runtime modes: scan for environment variables, CLI flags, or config files that switch behavior between `dev`, `prod`, `smoke`, `local`, `staging`, or `test` modes; record each mode and its activation mechanism.
3. For each mode, extract the configuration delta: what services are enabled/disabled, which env vars differ, what compose profiles are activated, and what feature flags change; record exact differences with evidence.
4. Build EXEC_MODE_DELTA_REPORT by comparing each non-production mode against the production baseline; highlight differences in services, ports, volumes, env vars, and security settings.
5. For each EXEC_RUNTIME_MODES item, populate `id`, mode name, activation mechanism, and `evidence`.
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
- Undocumented mode: if code branches on a mode value not documented in any README or config file, emit with `status: undocumented_mode` and evidence of the code branch.
- Production baseline unclear: if no explicit production configuration exists, use the most restrictive configuration as baseline and note the assumption in `coverage_notes`.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_E4 — RUNTIME MODES / DELTA REPORT

TASK: Identify runtime “modes” (dev/prod/smoke/local) + deltas.

OUTPUTS:
	•	EXEC_RUNTIME_MODES.json
	•	EXEC_MODE_DELTA_REPORT.json
```
