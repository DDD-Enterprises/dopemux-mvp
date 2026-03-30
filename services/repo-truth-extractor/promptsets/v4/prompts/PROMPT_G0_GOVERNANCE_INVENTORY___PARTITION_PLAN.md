# PROMPT_G0

## Goal
Produce `G0` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Focus on CI gates, policy enforcement, and governance drift risks.

## Inputs
- Source scope (scan these roots first):
- `.github/workflows/**`
- `pyproject.toml`
- `scripts/**`
- `config/**`
- `docs/90-adr/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G0`
    - `id_rule`: `GOV_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `GOV_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G0`
    - `id_rule`: `GOV_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan `.github/workflows/**`, `.pre-commit-config.yaml`, `CODEOWNERS`, `LICENSE`, `.gitignore`, and `pyproject.toml` for all governance and policy definitions.
2. Extract **CI Gates**: Identify job names, triggers, and success criteria in GitHub Actions that enforce quality bars.
3. Extract **Policy Files**: Inventory `LICENSE`, `CODEOWNERS`, and repo-level `.gitignore` rules for mandatory enforcement.
4. Extract **Environment Scoping**: Identify where `.env` or configuration files are loaded in scripts and entrypoints.
5. Catalog **Credential Loaders**: Locate code patterns that load secrets (e.g., `os.getenv`, `pydantic.BaseSettings`) without exposing values.
6. Build the partition plan by grouping governance items into cohesive partitions: CI, Hygiene, Policy, and Security.
7. Legacy Context is intent guidance only and is never evidence.
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
# PROMPT_G0 — GOVERNANCE INVENTORY + PARTITION PLAN

TASK: Build inventory and partition plan for the governance plane.

OUTPUTS:
	•	GOV_INVENTORY.json
	•	GOV_PARTITIONS.json
```
