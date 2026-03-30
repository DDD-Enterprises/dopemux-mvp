# PROMPT_B1

## Goal
Produce `B1` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
Focus on boundary enforcement points, refusal rails, and concrete bypass evidence.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/90-adr/**`
- `.claude/**`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `BOUNDARY_INVENTORY.json`
- `BOUNDARY_PARTITIONS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `BOUNDARY_ENFORCEMENT_POINTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `BOUNDARY_ENFORCEMENT_POINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B1`
    - `id_rule`: `BOUNDARY_ENFORCEMENT_POINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `BOUNDARY_INVENTORY.json` and `BOUNDARY_PARTITIONS.json` from upstream.
2. Extract **Enforcement Points**: Scan code for FastAPI `Depends(verify_...)`, `Security()`, or custom auth decorators that guard sensitive operations.
3. Map **Assertion Logic**: Identify the concrete check performed (e.g., token validation, role-based scope verification) with exact evidence.
4. Trace **Enforcement Context**: Link checks to the specific service or agent (from `AGENTS.md`) being protected.
5. Cross-reference with inventory to identify overrides, shadows, or gaps where a declared boundary lacks code enforcement.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_B1 — BOUNDARY ASSERTIONS / CODE ENFORCEMENT POINTS

TASK: Find boundary checks in code/config/docs (facts only).

OUTPUTS:
	•	BOUNDARY_ENFORCEMENT_POINTS.json
```
