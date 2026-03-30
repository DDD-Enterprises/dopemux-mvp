# PROMPT_T9

## Goal
Produce `T9` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`
- `TP_PACKETS_TOP10.partX.md`
- `TP_PACKET_IMPLEMENTATION_INDEX.json`
- `TP_SCHEMA.json`
- `TP_AUTHORITY_RULES.json`
- `TP_BATCHED_PACKETS.partX.md`
- `TP_BATCH_INDEX.json`
- `TP_DEDUPED.json`
- `TP_COLLISIONS.json`
- `TP_RUN_PLAN.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_INDEX.json`
- `TP_MERGED.json`
- `TP_QA.json`
- `TP_SUMMARY.md`
- `TP_BACKLOG_TOPN.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_SUMMARY.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_SUMMARY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `TP_BACKLOG_TOPN.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_BACKLOG_TOPN:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all T-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all TASK_* artifacts into TASK_PACKETS_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all T-Phase artifacts present, coverage complete, sort order deterministic; emit TASK_PACKETS_QA
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
# PROMPT_T9 — MERGE / QA

TASK: Merge all Phase T packet artifacts, run QA, and emit canonical Task Packet outputs.

OUTPUTS:
- TP_INDEX.json
- TP_MERGED.json
- TP_QA.json
- TP_SUMMARY.md
- TP_BACKLOG_TOPN.json

QA requirements:
- Validate required schema fields for every packet.
- Validate implementer target, evidence paths, and acceptance/rollback completeness.
- Emit missing-evidence list and unresolved-collision list.
- Emit packet counts by priority and dependency tier.
- Fail closed if required canonical outputs cannot be produced.
```
