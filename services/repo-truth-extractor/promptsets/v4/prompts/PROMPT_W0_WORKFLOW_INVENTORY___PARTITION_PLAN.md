# PROMPT_W0

## Goal
Produce `W0` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W0`
    - `id_rule`: `WORKFLOW_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `WORKFLOW_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W0`
    - `id_rule`: `WORKFLOW_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan workflow sources (orchestration scripts, runbooks, CI workflows, compose, tmux sessions) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the workflow sources (orchestration scripts, runbooks, CI workflows, compose, tmux sessions) domain
3. Build WORKFLOW_PARTITIONS by grouping files into logical categories with rationale
4. For each WORKFLOW_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each WORKFLOW_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
# PROMPT_W0 — WORKFLOW INVENTORY + PARTITION PLAN

TASK: Build inventory and partition plan for workflows.

OUTPUTS:
	•	WORKFLOW_INVENTORY.json
	•	WORKFLOW_PARTITIONS.json
```
