# PROMPT_Q9

## Goal
Produce `Q9` outputs for phase `Q` with strict schema, explicit evidence, and deterministic normalization.
Focus on coverage, collisions, determinism drift, and recovery actions.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `services/repo-truth-extractor/**`
- `services/registry.yaml`
- `compose.yml`
- `docker-compose*.yml`
- Upstream normalized artifacts available to this step:
- `QA_RUN_MANIFEST.json`
- `QA_MISSING_ARTIFACTS.json`
- `QA_PROMPT_COLLISIONS.json`
- `QA_NORM_DRIFT_REPORT.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PIPELINE_DOCTOR_REPORT.json`
- `QA_SERVICE_COVERAGE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `PIPELINE_DOCTOR_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Q9`
    - `id_rule`: `PIPELINE_DOCTOR_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `QA_SERVICE_COVERAGE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `single_payload`
    - `canonical_writer_step_id`: `Q9`
    - `id_rule`: `QA_SERVICE_COVERAGE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`

## Extraction Procedure
1. Load all Q-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all QA_* artifacts into PIPELINE_DOCTOR_REPORT using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all Q-Phase artifacts present, coverage complete, sort order deterministic; emit QA_SERVICE_COVERAGE
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
# PROMPT_Q9 — Pipeline doctor merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge pipeline doctor outputs into a single report.

OUTPUTS:
  • PIPELINE_DOCTOR_REPORT.json

RULES:
  • Maintain deterministic ordering and mark any empty sections explicitly.
```
