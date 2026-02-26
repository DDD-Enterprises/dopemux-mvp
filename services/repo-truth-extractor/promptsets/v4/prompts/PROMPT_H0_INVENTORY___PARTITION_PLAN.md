# PROMPT_H0

## Goal
Produce `H0` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H0`
    - `id_rule`: `HOME_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H0`
    - `id_rule`: `HOME_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan home control-plane dirs (`~/.claude/`, `~/.config/`, shell profiles, dotfiles) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the home control-plane dirs (`~/.claude/`, `~/.config/`, shell profiles, dotfiles) domain
3. Build HOME_PARTITIONS by grouping files into logical categories with rationale
4. For each HOME_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each HOME_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
- Sensitive file: if a home file may contain secrets, reference by path only; emit with `kind: sensitive` and `content: REDACTED`
- Missing home dir: if the home scan target does not exist, emit with `status: inaccessible`

## Legacy Context (for intent only; never as evidence)
```markdown
# Phase H0: Home Control Plane Inventory + Partition Plan

You are running inside the Dopemux extraction pipeline.

Goal:
- Inventory only the HOME control-plane relevant files found in the provided context.
- Produce a deterministic partition plan for subsequent Phase H steps.

Hard rules:
- Do NOT invent paths or contents not present in the provided context.
- If something is commonly expected (~/.config/mcp, ~/.dopemux) but not present in context, record it as MISSING (not guessed).
- Output valid JSON only, no markdown fences.

Inputs:
- The runner provides a set of home-control-plane candidate files (safe mode filtering may already have excluded sensitive areas).

Outputs:
- HOME_INVENTORY.json
- HOME_PARTITIONS.json

HOME_INVENTORY.json format:
{
  "inventory_version": "H0.v1",
  "generated_at": "<iso8601>",
  "root_hint": "<string or empty>",
  "items": [
    {
      "path": "<string>",
      "ext": "<string>",
      "bytes": <int>,
      "mtime_epoch": <int>,
      "category_hint": "<one of: mcp|router|litellm|profiles|tmux|sqlite|shell|other|unknown>",
      "notes": "<string>"
    }
  ],
  "missing_expected_roots": [
    {"path": "<string>", "reason": "<string>"}
  ]
}

HOME_PARTITIONS.json format:
{
  "partition_version": "H0.v1",
  "generated_at": "<iso8601>",
  "max_files_per_partition": <int>,
  "partitions": [
    {
      "partition_id": "H_P0001",
      "focus": "<mcp|router|litellm|profiles|tmux|sqlite|mixed>",
      "paths": ["<path1>", "<path2>"],
      "notes": "<string>"
    }
  ],
  "determinism_notes": [
    "Paths sorted ascending before partitioning
```
