# PROMPT_M0

## Goal
Produce `M0` outputs for phase `M` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/**`
- `docker/**`
- `extraction/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `M0_RUNTIME_EXPORT_INVENTORY.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `M0_RUNTIME_EXPORT_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `M0`
    - `id_rule`: `M0_RUNTIME_EXPORT_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan allowlisted home roots (`~/.dopemux/**`, `~/.config/dopemux/**`, `~/.config/taskx/**`, `~/.config/litellm/**`) as represented in the provided context. For each file found, record: path, file kind (config, database, log, state), size, and modification indicator with evidence.
2. Classify each runtime store by function: configuration surface (YAML/JSON configs), state database (SQLite, LevelDB), log output, cache directory, and credential reference. Record classification with evidence.
3. For database files, record the database engine (SQLite, etc.) and file path. For config files, extract top-level keys as a content summary. Never extract secret values.
4. Validate that all discovered files fall within the allowlisted roots; emit `status: out_of_scope` for any file outside the allowed paths.
5. Legacy Context is intent guidance only and is never evidence.
6. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
7. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
8. Attach evidence to every non-derived field and every relationship edge.
9. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
10. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
11. Emit exactly the declared outputs and no additional files.

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
- Allowlisted root directory does not exist in the provided context: emit with `status: root_not_found` and evidence.
- File within allowlisted root is a symlink pointing outside the allowed scope: emit with `status: external_symlink` and the link target path.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: M0_RUNTIME_EXPORT_INVENTORY.json

Prompt:
- Task: detect runtime stores and config surfaces only within allowlisted home roots:
  - ~/.dopemux/**
  - ~/.config/dopemux/**
  - ~/.config/taskx/**
  - ~/.config/litellm/**
  - ~/.config/mcp/**
- Identify likely state stores: *.sqlite, *.sqlite3, *.db, context.db, global_index.sqlite.
- Output fields must include for each path:
  - path, size, mtime, classification (sqlite_db|config|cache|unknown), exportability (ok|permission_denied|missing_tool|unsafe).
- Hard rules:
  - No full file content dumps.
  - If caps are hit, emit TRUNCATED marker and counts.
  - Do not include secrets, tokens, or raw message content.
```
