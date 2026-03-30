# PROMPT_G2

## Goal
Produce `G2` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Focus on CI gates, policy enforcement, and governance drift risks.

## Inputs
- Source scope (scan these roots first):
- `.github/workflows/**`
- `pyproject.toml`
- `scripts/**`
- `config/**`
- `docs/90-adr/**`
- Upstream normalized artifacts available to this step:
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`
- `GOV_CI_GATES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_HYGIENE_POLICIES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_HYGIENE_POLICIES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G2`
    - `id_rule`: `GOV_HYGIENE_POLICIES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `GOV_INVENTORY.json` and `GOV_PARTITIONS.json` from upstream.
2. Extract **Hygiene Rules**: Parse `.gitignore` for forbidden patterns and `.pre-commit-config.yaml` for mandatory hooks.
3. Map **Allowlists**: Identify explicitly permitted exceptions in policy files or linter configs (e.g., `.eslintignore`) with evidence.
4. Trace **Enforcement Scripts**: Locate any `scripts/` or `Make` targets that perform "lint-like" repo hygiene checks.
5. Identify **Drift**: Flag any files in the repo that violate the current `.gitignore` or `CODEOWNERS` rules.
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
# PROMPT_G2 — REPO HYGIENE / ALLOWLISTS / POLICIES

TASK: Extract repo hygiene policies and allowlists.

OUTPUTS:
	•	GOV_HYGIENE_POLICIES.json
```
