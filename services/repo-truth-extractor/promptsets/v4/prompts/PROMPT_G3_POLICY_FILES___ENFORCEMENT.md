# PROMPT_G3

## Goal
Produce `G3` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
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
- `GOV_HYGIENE_POLICIES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_POLICIES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_POLICIES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G3`
    - `id_rule`: `GOV_POLICIES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `GOV_INVENTORY.json`, `GOV_CI_GATES.json`, and `GOV_HYGIENE_POLICIES.json`.
2. Extract **Policy Enforcement Paths**: Connect policy declarations (e.g., `LICENSE`) to concrete CI gates or pre-commit hooks.
3. Map **Authority Owners**: Link specific files/folders to owners identified in `CODEOWNERS` with exact evidence.
4. Document **Escalation Rails**: Trace how policy violations are reported and to whom (based on `CODEOWNERS` or PR templates).
5. Resolve **Conflicting Policies**: If multiple policies apply to the same scope, apply the most restrictive rule and cite both.
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
# PROMPT_G3 — Policy files + enforcement

ROLE: Governance extractor.
GOAL: catalog policy files and the enforcement mechanisms they trigger.

OUTPUTS:
  • GOV_POLICIES.json

RULES:
  • Document each policy file and any hooks/scripts that enforce it.
```
