# PROMPT_D0

## Goal
Produce `D0` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `docs/docs_index.yaml`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_INVENTORY.json`
- `DOC_PARTITIONS.json`
- `DOC_TODO_QUEUE.json`

## Hard Output Contract
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited `line_range` MUST use the line numbers shown in the provided excerpt.
- Every `items[]` entry MUST include `id`, `path`, and `line_range`.
- Every evidence object MUST include repo-relative `path`, integer `line_range`, and exact `excerpt`.
- If a value cannot be grounded from the provided excerpt, return valid JSON with `UNKNOWN` or fail-closed placeholders; never invent line numbers.

## Hard Requirements
- Every `payload.items[]` row MUST include:
  - `id` as a string
  - `path` as a repo-relative string
  - `line_range` as `[start, end]` with exactly two integers where `start > 0` and `end >= start`
- For every emitted row, `evidence[0].path` and `evidence[0].line_range` MUST match the row's `path` and `line_range`.
- Treat the provided excerpts as line-numbered evidence. Cite only those excerpt-local line numbers.
- If you cannot determine a real `line_range` from the provided evidence, do not guess.
- Instead, emit a valid artifact envelope with `"items": []` for that artifact.
- Output exactly one JSON object. No markdown, no prose, no code fences.

## Minimal Example
```json
{
  "artifacts": [
    {
      "artifact_name": "DOC_INVENTORY.json",
      "payload": {
        "schema": "DOC_INVENTORY@v1",
        "items": [
          {
            "id": "DOC_INVENTORY:example",
            "path": "docs/example.md",
            "line_range": [4, 6],
            "kind": "guide",
            "summary": "Example inventory row.",
            "evidence": [
              {
                "path": "docs/example.md",
                "line_range": [4, 6],
                "excerpt": "0004: Example heading"
              }
            ]
          }
        ]
      }
    }
  ]
}
```

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D0`
    - `id_rule`: `DOC_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D0`
    - `id_rule`: `DOC_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_TODO_QUEUE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D0`
    - `id_rule`: `DOC_TODO_QUEUE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan documentation (`docs/**`, archive dirs) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the documentation (`docs/**`, archive dirs) domain
3. Build DOC_PARTITIONS by grouping files into logical categories with rationale
4. For each DOC_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each DOC_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
- Policy without enforcement: if a policy exists but nothing enforces it, emit with `status: unenforced`
- Overlapping artifacts: if multiple files cover the same concern, emit all with `status: overlapping`

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: DOC_INVENTORY.json, DOC_PARTITIONS.json, DOC_TODO_QUEUE.json

Prompt:
- Scan docs/** (include archive dirs but tag them as archive).
- For each doc:
  - path, size, mtime, top headings, first 40 non-empty lines, token count estimate.
  - tag: ACTIVE vs ARCHIVE vs QUARANTINE based on path + in-doc markers.
- Create partitions:
  - core architecture
  - planes (pm/memory/orchestrator/mcp/hooks)
  - services (dope-memory, eventbus, dashboards, etc.)
  - task-packets + governance
  - research/audits
  - archives (split into manageable buckets)
- Output a queue of partitions with recommended run order.
```
