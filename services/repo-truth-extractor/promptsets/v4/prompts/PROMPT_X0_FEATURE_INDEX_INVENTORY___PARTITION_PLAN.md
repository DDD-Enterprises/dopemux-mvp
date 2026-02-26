# PROMPT_X0

## Goal
Produce `X0` outputs for phase `X` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/**`
- `README.md`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FEATURE_INDEX_INVENTORY.json`
- `FEATURE_INDEX_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FEATURE_INDEX_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X0`
    - `id_rule`: `FEATURE_INDEX_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FEATURE_INDEX_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `X0`
    - `id_rule`: `FEATURE_INDEX_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan `src/**`, `services/**`, `docs/**`, and `README.md` as specified in the inputs section. Build a feature index inventory by identifying user-visible features, internal capabilities, and integration points from code entry points, API routes, CLI commands, UI components, and documented feature descriptions.
2. For each feature candidate, extract: feature name, type (user-facing/internal/integration), owning service or module, primary entry points, and a one-line summary with evidence from code or documentation.
3. Partition features deterministically for downstream X1-X4 extraction steps, grouping by service boundary and feature domain. Assign stable partition IDs based on service_id and feature name.
4. Structure the output with clear inventory entries with evidence citations, partition assignments with rationale, and an explicit UNKNOWN section for code or doc references that may indicate features but cannot be confirmed.
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
- Feature candidate identified from documentation only with no corresponding code entry point: classify as `status: doc_only` with evidence and flag for verification against code.
- Service boundary for feature partitioning is ambiguous (feature spans multiple services): assign to primary service by evidence density and record secondary services in `cross_service_refs`.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_X0_FEATURE_INDEX_INVENTORY___PARTITION_PLAN

TASK: Build feature-index inventory and deterministic partition plan.

SCAN TARGETS:
- services/
- src/
- docs/
- config/
- scripts/
- Makefile
- docker-compose*.yml

OUTPUTS:
- FEATURE_INDEX_INVENTORY.json
- FEATURE_INDEX_PARTITIONS.json

RULES:
- Enumerate candidate feature surfaces, owning code paths, and related docs.
- Partition deterministically for downstream X1 extraction.
- Preserve literal evidence and source paths.
```
