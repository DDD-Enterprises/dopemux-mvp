# PROMPT_T2

## Goal
Produce `T2` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_SCHEMA.json`
- `TP_AUTHORITY_RULES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_SCHEMA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T2`
    - `id_rule`: `TP_SCHEMA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_AUTHORITY_RULES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T2`
    - `id_rule`: `TP_AUTHORITY_RULES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream extraction artifacts and synthesis reports as input for packet schema and authority rules
2. Analyze extraction outputs to identify actionable work items for PACKET_SCHEMA_RULES
3. For each task packet, determine scope, priority, dependencies, and acceptance criteria from evidence
4. Validate packet completeness: ensure each packet has sufficient context for execution
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
# PROMPT_T2 — PACKET SCHEMA / AUTHORITY RULES

TASK: Define the canonical Task Packet schema and authority hierarchy used by Phase T.

OUTPUTS:
- TP_SCHEMA.json
- TP_AUTHORITY_RULES.json

Rules:
- implementer_target must be exactly `Codex Desktop (GPT-5.3-Codex)`.
- Authority hierarchy is strict: R norm artifacts > X norm artifacts > policy docs.
- Every packet must include evidence-backed `authority_inputs` paths.
- No packet may require re-scan, truth reinterpretation, or undocumented assumptions.
- Define required fields, validation constraints, and failure reasons for schema noncompliance.
```
