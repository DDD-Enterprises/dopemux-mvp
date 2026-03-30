# PROMPT_D4

## Goal
Produce `D4` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_INDEX.json`
- `DOC_CONTRACT_CLAIMS.json`
- `DOC_SUPERSESSION.json`
- `DOC_TOPIC_CLUSTERS.json`
- `DUPLICATE_DRIFT_REPORT.json`
- `DOC_RECENCY_DUPLICATE_REPORT.json`
- `DOC_COVERAGE_REPORT.json`

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
  - `DOC_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DOC_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_CONTRACT_CLAIMS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DOC_CONTRACT_CLAIMS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_SUPERSESSION.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DOC_SUPERSESSION:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_TOPIC_CLUSTERS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D5`
    - `id_rule`: `DOC_TOPIC_CLUSTERS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DUPLICATE_DRIFT_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DUPLICATE_DRIFT_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_RECENCY_DUPLICATE_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DOC_RECENCY_DUPLICATE_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOC_COVERAGE_REPORT.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D4`
    - `id_rule`: `DOC_COVERAGE_REPORT:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, missing, extra, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all D-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all DOC_* artifacts into DOC_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all D-Phase artifacts present, coverage complete, sort order deterministic; emit DOC_QA
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
Goal:
- merged: DOC_INDEX.json, DOC_CONTRACT_CLAIMS.json, DOC_SUPERSESSION.json, DOC_TOPIC_CLUSTERS.json, DUPLICATE_DRIFT_REPORT.json
- optional alternate duplicate artifact: DOC_RECENCY_DUPLICATE_REPORT.json
- QA: DOC_COVERAGE_REPORT.json

Prompt:
- Merge all part files.
- Dedup rules:
  - prefer newer timestamps when same doc appears in multiple buckets
  - preserve both if content differs materially
- Coverage gates:
  - all docs indexed
  - no pending partitions
  - all CAP_NOTICES resolved or explicitly waived
  - citation graph present
```
