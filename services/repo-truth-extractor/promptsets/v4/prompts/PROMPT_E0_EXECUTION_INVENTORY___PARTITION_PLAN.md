# PROMPT_E0

## Goal
Produce `E0` outputs for phase `E` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `compose.yml`
- `docker-compose*.yml`
- `Makefile`
- `src/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `EXEC_INVENTORY.json`
- `EXEC_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `EXEC_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E0`
    - `id_rule`: `EXEC_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `EXEC_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `E0`
    - `id_rule`: `EXEC_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan execution-plane targets (`Makefile`, `scripts/`, `*.sh`, `.github/`, `docker*/`) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the execution-plane targets (`Makefile`, `scripts/`, `*.sh`, `.github/`, `docker*/`) domain
3. Build EXEC_PARTITIONS by grouping files into logical categories with rationale
4. For each EXEC_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each EXEC_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
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
# PROMPT_E0 — EXECUTION INVENTORY + PARTITION PLAN

TASK: Build inventory + partitions for execution plane.
SCAN TARGETS: Makefile, package.json, pyproject.toml, scripts/, tools/, compose/, .github/, docker*/, *.sh, *.zsh, justfile*, *.mk.

OUTPUTS:
	•	EXEC_INVENTORY.json
	•	EXEC_PARTITIONS.json

RULES:
	•	Identify every file in the scan targets.
	•	Chunk sources into tractable partitions for the following prompts.
	•	Ensure partitions are deterministic.
```
