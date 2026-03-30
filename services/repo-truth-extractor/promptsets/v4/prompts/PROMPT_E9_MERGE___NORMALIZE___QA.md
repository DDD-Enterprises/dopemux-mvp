# PROMPT_E9

## Goal
Produce `E9` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `compose.yml`
- `docker-compose*.yml`
- `Makefile`
- `src/**`
- Upstream normalized artifacts available to this step:
- `EXEC_INVENTORY.json`
- `EXEC_PARTITIONS.json`
- `EXEC_BOOTSTRAP_COMMANDS.json`
- `EXEC_ENV_CHAIN.json`
- `EXEC_STARTUP_GRAPH.json`
- `EXEC_RUNTIME_MODES.json`
- `EXEC_MODE_DELTA_REPORT.json`
- `EXEC_ARTIFACT_SURFACE.json`
- `EXEC_RISK_FACTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_MERGED.json`
- `EXEC_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E9`
    - `id_rule`: `EXEC_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `EXEC_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E9`
    - `id_rule`: `EXEC_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all E-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all EXEC_* artifacts into EXEC_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all E-Phase artifacts present, coverage complete, sort order deterministic; emit EXEC_QA
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
# PROMPT_E9 — Execution merge + normalize + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge all EXEC_* outputs, report coverage and suspicious gaps.

OUTPUTS:
  • EXEC_MERGED.json
  • EXEC_QA.json (counts_by_filekind, partitions_covered, missing_expected_outputs[], suspicious_empty[])

RULES:
  • Normalize arrays by stable sort, remove duplicate rows.
  • Preserve exact field names from upstream prompts.
```
