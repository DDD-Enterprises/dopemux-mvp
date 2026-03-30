# PROMPT_W9

## Goal
Produce `W9` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`
- `WORKFLOW_CATALOG.json`
- `WORKFLOW_IO_MAP.json`
- `WORKFLOW_COORDINATION_SURFACE.json`
- `WORKFLOW_FAILURE_RECOVERY.json`
- `WORKFLOW_STATE_COUPLING.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_MERGED.json`
- `WORKFLOW_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W9`
    - `id_rule`: `WORKFLOW_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `WORKFLOW_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W9`
    - `id_rule`: `WORKFLOW_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all W-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all WORKFLOW_* artifacts into WORKFLOW_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all W-Phase artifacts present, coverage complete, sort order deterministic; emit WORKFLOW_QA
4. Cross-check coverage: verify every inventory item has corresponding extraction entries
5. For each output item, populate `id`, required fields, and `evidence` per schema contracts
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
# PROMPT_W9 — Workflows merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge workflow artifacts and report coverage.

OUTPUTS:
  • WORKFLOW_MERGED.json
  • WORKFLOW_QA.json

RULES:
  • Normalize arrays by stable sort and remove duplicates.
```
