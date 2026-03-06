# PROMPT_B0

## Goal
Produce `B0` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
Focus on boundary enforcement points, refusal rails, and concrete bypass evidence.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/90-adr/**`
- `.claude/**`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `BOUNDARY_INVENTORY.json`
- `BOUNDARY_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `BOUNDARY_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B0`
    - `id_rule`: `BOUNDARY_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `BOUNDARY_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B0`
    - `id_rule`: `BOUNDARY_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan `src/**`, `services/**`, `docs/90-adr/**`, `.claude/**`, and `AGENTS.md` for all API surface definitions, endpoint declarations, route registrations, middleware chains, and MCP tool manifests.
2. For each discovered endpoint or boundary point, extract: protocol (HTTP/gRPC/MCP/CLI), path or method signature, input validation constraints, authentication requirements, and rate limit annotations with exact file:line evidence.
3. Catalog all refusal rails and authorization guard clauses by tracing decorator chains, middleware stacks, and policy enforcement functions; record the guard condition, protected resource, and bypass risk.
4. Cross-reference discovered boundaries against `services/registry.yaml` to assign each boundary to its canonical service_id; flag any boundary not attributable to a registered service.
5. Build the partition plan by grouping boundary items into cohesive partitions based on owning service, protocol family, and directory locality; assign each partition a stable `partition_id` derived from `SHA256(sorted(file_paths))`.
6. For each BOUNDARY_INVENTORY item, populate `id` using `BOUNDARY_INVENTORY:<stable-hash(path|symbol|name)>`, `path`, `kind` (endpoint|guard|policy|middleware), `summary`, and `evidence` array with repo-relative paths, line ranges, and exact excerpts.
7. For each BOUNDARY_PARTITIONS item, populate `id` using `BOUNDARY_PARTITIONS:<stable-hash(path|symbol|name)>`, `partition_id`, `files` (sorted list), `reason`, and `evidence`.
8. Legacy Context is intent guidance only and is never evidence.
9. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
10. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.

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
- Boundary without owning service: if a discovered endpoint or guard cannot be attributed to any service in `services/registry.yaml`, keep the item with `service_id: UNKNOWN` and `missing_evidence_reason` citing the registry gap.
- Partition overlap: if a file contains boundaries belonging to multiple logical partitions, assign to the partition with the most boundary items in that file and record the conflict in `coverage_notes`.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_B0 — BOUNDARY INVENTORY + PARTITION PLAN

TASK: Build inventory and partition plan for the boundary plane.

OUTPUTS:
	•	BOUNDARY_INVENTORY.json
	•	BOUNDARY_PARTITIONS.json
```
