# PROMPT_C0

## Goal
Produce `C0` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Focus on service runtime truths, interfaces, dependencies, and code-level ownership.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docker/**`
- `compose.yml`
- `docker-compose*.yml`
- `services/registry.yaml`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `CODE_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C0`
    - `id_rule`: `CODE_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, line_range, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `CODE_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C0`
    - `id_rule`: `CODE_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, path, line_range, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan source code (`services/`, `src/`, `lib/`, `scripts/`, `tools/`) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the source code (`services/`, `src/`, `lib/`, `scripts/`, `tools/`) domain
3. Build CODE_PARTITIONS by grouping files into logical categories with rationale
4. For each `CODE_INVENTORY` item, populate `id`, `path`, `line_range`, `kind`, `summary`, and `evidence`.
5. For each `CODE_PARTITIONS` item, populate `id`, `partition_id`, `path`, `line_range`, `files` (sorted), `reason`, and `evidence`.
6. Wrap all items in the `ItemList` envelope: `{"schema":"json_item_list@v1","items":[...]}`.
7. Legacy Context is intent guidance only and is never evidence.
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
- Policy without enforcement: if a policy exists but nothing enforces it, emit with `status: unenforced`
- Overlapping artifacts: if multiple files cover the same concern, emit all with `status: overlapping`

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: CODE_INVENTORY.json, CODE_PARTITIONS.json

Prompt:
- Build partitions by subsystem:
  - services/** entrypoints
  - shared/**
  - src/**
  - workflow scripts
  - eventbus modules
  - dope-memory modules
  - boundary/guardrail modules
  - taskx bridges
```
