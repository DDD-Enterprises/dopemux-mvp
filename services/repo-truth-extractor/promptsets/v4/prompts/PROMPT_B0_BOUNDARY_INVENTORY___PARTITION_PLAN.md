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
1. Scan `src/**`, `services/**`, `docs/90-adr/**`, `.claude/settings.json`, and `AGENTS.md` for all API surface definitions, FastAPI `Depends()` auth enforcements, tool permissions, and agent declarations.
2. For each discovered endpoint or boundary point, extract: protocol (HTTP/MCP/CLI), method signature, input validation, authentication requirements, and rate limit annotations with exact evidence.
3. Catalog all **Refusal Rails** and authorization guard clauses by tracing `raise HTTPException`, decorator chains, and policy enforcement functions in `.claude/settings.json`.
4. Inventory **Agent Boundaries**: Extract role-based access control (RBAC) and tool-use constraints declared in `AGENTS.md`.
5. Cross-reference discovered boundaries against `services/registry.yaml` to assign each boundary to its canonical service_id.
6. Build the partition plan by grouping boundary items into cohesive partitions based on owning service, protocol family, and directory locality.
7. Legacy Context is intent guidance only and is never evidence.
9. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
10. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_B0 — BOUNDARY INVENTORY + PARTITION PLAN

TASK: Build inventory and partition plan for the boundary plane.

OUTPUTS:
	•	BOUNDARY_INVENTORY.json
	•	BOUNDARY_PARTITIONS.json
```
