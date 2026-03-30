# PROMPT_W1

## Goal
Produce `W1` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_CATALOG.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_CATALOG.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W1`
    - `id_rule`: `WORKFLOW_CATALOG:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the workflow catalog and runbook partition as primary scan surface.
2. Identify executable workflows in `scripts/**`: scan for `main()` entrypoints in Python/Ruby scripts and `set -e` blocks in Shell scripts that define multi-step sequences.
3. Locate runbook facts in `docs/02-how-to/**` and `docs/03-reference/**`: search for step-by-step instructions and command blocks (marked with ` ``` `).
4. Extract literal steps: for each identified workflow, list the specific commands or function calls executed in sequence, along with their prerequisites.
5. Scan `compose.yml` for multi-service `command:` overrides that define specific runtime workflows (e.g., `seed-db`, `run-tests`).
6. Build relationship graph: link documentation runbooks to their corresponding executable script files and service entrypoints.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in workflow definitions.
8. For each WORKFLOW_CATALOG item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID.
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

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
- Hidden dependency: if an element depends on something not explicitly documented, emit with `status: implicit_dependency`
- Shadowed config: if a config overrides another at a different level, emit both with `status: shadow`

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_W1 — WORKFLOW CATALOG / RUNBOOK FACTS

TASK: Enumerate workflows W1..Wn with literal steps.

OUTPUTS:
	•	WORKFLOW_CATALOG.json
```
