# PROMPT_D2

## Goal
Produce `D2` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_INTERFACES.partX.json`
- `DOC_WORKFLOWS.partX.json`
- `DOC_DECISIONS.partX.json`
- `DOC_GLOSSARY.partX.json`

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
  - `DOC_INTERFACES.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_INTERFACES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_WORKFLOWS.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_WORKFLOWS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_DECISIONS.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_DECISIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_GLOSSARY.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_GLOSSARY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load upstream inventory and partitions; use the deep doc extraction (interfaces, workflows, decisions) partition as primary scan surface
2. Extract deep doc extraction (interfaces, workflows, decisions) facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted deep doc extraction (interfaces, workflows, decisions) elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each DOC_DEEP item, populate `id`, required fields, and `evidence`
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
Goal (per partition):
- DOC_INTERFACES.partX.json
- DOC_WORKFLOWS.partX.json
- DOC_DECISIONS.partX.json
- DOC_GLOSSARY.partX.json

Prompt:
- Extract structured interface/workflow details:
  - service responsibilities
  - dataflow steps
  - event names mentioned
  - state DBs and schema references
  - operational workflows, multi-service pipelines
  - instruction-file-driven workflows
- Again: cite everything.
```
