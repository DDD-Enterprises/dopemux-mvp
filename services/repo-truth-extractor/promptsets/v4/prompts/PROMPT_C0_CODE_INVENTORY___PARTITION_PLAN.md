# PROMPT_C0

## Goal
Produce `C0` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Focus on service runtime truths, interfaces, dependencies, and code-level ownership.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `components/**`
- `dashboard/**`
- `plugins/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `compose/**`
- `config/**`
- `configs/**`
- `contracts/**`
- `docker/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `profiles/**`
- `review_artifacts/**`
- `scripts/**`
- `shared/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `tools/**`
- `UPGRADES/**`
- `vendor/**`


- `services/agents/**`
- `src/dopemux/hooks/**`
- `src/dopemux/agent_orchestrator.py`
- `extraction/**`
- `reports/**`




- `compose.yml`
- `docker-compose*.yml`
- `services/registry.yaml`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `CODE_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C0`
    - `id_rule`: `CODE_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `CODE_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C0`
    - `id_rule`: `CODE_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan source code (`services/`, `src/`, `lib/`, `scripts/`, `tools/`) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the source code (`services/`, `src/`, `lib/`, `scripts/`, `tools/`) domain
3. Build CODE_PARTITIONS by grouping files into logical categories with rationale
4. For each CODE_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each CODE_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
Goal: CODE_INVENTORY.json, CODE_PARTITIONS.json

Prompt:
- Build partitions by subsystem:
  - services/** entrypoints
  - shared/**
  - src/**
  - workflow scripts
  - eventbus modules
  - dope-memory modules
  - boundary/guardrail modules
  - taskx bridges
```
