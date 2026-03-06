# PROMPT_D5

## Goal
Produce `D5` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `docs/docs_index.yaml`
- Upstream normalized artifacts available to this step:
- `DOC_INVENTORY.json`
- `DOC_PARTITIONS.json`
- `DOC_TODO_QUEUE.json`
- `DOC_INDEX.partX.json`
- `DOC_CONTRACT_CLAIMS.partX.json`
- `DOC_BOUNDARIES.partX.json`
- `DOC_SUPERSESSION.partX.json`
- `CAP_NOTICES.partX.json`
- `DOC_INTERFACES.partX.json`
- `DOC_WORKFLOWS.partX.json`
- `DOC_DECISIONS.partX.json`
- `DOC_GLOSSARY.partX.json`
- `DOC_CITATION_GRAPH.json`
- `DOC_INDEX.json`
- `DOC_CONTRACT_CLAIMS.json`
- `DOC_SUPERSESSION.json`
- `DOC_TOPIC_CLUSTERS.json`
- `DUPLICATE_DRIFT_REPORT.json`
- `DOC_RECENCY_DUPLICATE_REPORT.json`
- `DOC_COVERAGE_REPORT.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_TOPIC_CLUSTERS.json`

## Hard Output Contract
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited `line_range` MUST use the line numbers shown in the provided excerpt.
- Every `items[]` entry MUST include `id`, `path`, and `line_range`.
- Every evidence object MUST include repo-relative `path`, integer `line_range`, and exact `excerpt`.
- If a value cannot be grounded from the provided excerpt, return valid JSON with `UNKNOWN` or fail-closed placeholders; never invent line numbers.

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_TOPIC_CLUSTERS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D5`
    - `id_rule`: `DOC_TOPIC_CLUSTERS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the doc topic clustering partition as primary scan surface
2. Extract doc topic clustering facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted doc topic clustering elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each DOC_TOPIC_CLUSTERS item, populate `id`, required fields, and `evidence`
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
- Hidden dependency: if an element depends on something not explicitly documented, emit with `status: implicit_dependency`
- Shadowed config: if a config overrides another at a different level, emit both with `status: shadow`

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: DOC_TOPIC_CLUSTERS.json

Prompt:
- Input: merged docs index (plus optionally raw text samples).
- Cluster by token overlap (no semantic labeling).
- Output:
  - cluster_id
  - doc_paths
  - top_tokens (weighted)
  - doc_count
  - newest_mtime + oldest_mtime (for recency awareness)
- No "this cluster is architecture" labeling.
```
