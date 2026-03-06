# PROMPT_E0

## Goal
Produce `E0` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `compose.yml`
- `docker-compose*.yml`
- `Makefile`
- `src/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_INVENTORY.json`
- `EXEC_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E0`
    - `id_rule`: `EXEC_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `EXEC_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E0`
    - `id_rule`: `EXEC_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan execution-plane targets: `Makefile`, `package.json`, `pyproject.toml`, `scripts/`, `tools/`, `compose/`, `.github/`, `docker*/`, `*.sh`, `*.zsh`, `justfile*`, `*.mk`; collect path, type, and content metadata.
2. For each executable artifact, classify by kind: make-target, npm-script, shell-script, Python-script, compose-command, GitHub-action, or justfile-recipe; record the invocation syntax and dependencies.
3. Build EXEC_PARTITIONS by grouping execution artifacts into logical categories: build scripts, test runners, deployment scripts, development helpers, CI/CD workflows, and setup/bootstrap scripts.
4. For each EXEC_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`.
5. For each EXEC_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`.
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
- Makefile recursive include: if a Makefile includes other Makefiles that define additional targets, trace through includes and emit targets from all files with evidence of the include chain.
- Non-executable script: if a script file lacks execute permissions or a shebang line, emit with `status: non_executable` and evidence.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_E0 — EXECUTION INVENTORY + PARTITION PLAN

TASK: Build inventory + partitions for execution plane.
SCAN TARGETS: Makefile, package.json, pyproject.toml, scripts/, tools/, compose/, .github/, docker*/, *.sh, *.zsh, justfile*, *.mk.

OUTPUTS:
	•	EXEC_INVENTORY.json
	•	EXEC_PARTITIONS.json

RULES:
	•	Identify every file in the scan targets.
	•	Chunk sources into tractable partitions for the following prompts.
	•	Ensure partitions are deterministic.
```
