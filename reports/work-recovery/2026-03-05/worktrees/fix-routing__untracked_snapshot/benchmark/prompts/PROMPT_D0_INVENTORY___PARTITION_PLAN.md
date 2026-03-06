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
1. Scan `docs/**` including archive directories; for each document file collect `path`, `size`, `mtime`, top headings (H1-H3), first 40 non-empty lines, and token count estimate.
2. Tag each document with `status`: active, archive, or draft based on directory location and file metadata; archive documents in `docs/archive/**` or `docs/old/**` receive `status: archive`.
3. Build DOC_PARTITIONS by grouping documents by topic area (ADRs, runbooks, API docs, design specs, README files, guides); assign `partition_id` derived from the topic classification.
4. Build DOC_TODO_QUEUE by identifying documents with incomplete sections: look for TODO markers, FIXME comments, empty sections, placeholder text, and stub headings; record each with file:line evidence.
5. For each DOC_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`.
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
- Non-markdown doc: if a document is in a non-parseable format (PDF, DOCX, image), emit with `kind: binary_doc` and `content: UNKNOWN` with `missing_evidence_reason`.
- Archive with active references: if an archived document is referenced by active documents or code, flag in DOC_TODO_QUEUE with evidence of the stale reference.

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
