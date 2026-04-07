# PROMPT_G9

## Goal
Produce `G9` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
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
- `GOV_POLICIES.json`
- `GOV_SECRETS_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_MERGED.json`
- `GOV_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G9`
    - `id_rule`: `GOV_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `GOV_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G9`
    - `id_rule`: `GOV_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all G-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all GOV_* artifacts into GOV_MERGED using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all G-Phase artifacts present, coverage complete, sort order deterministic; emit GOV_QA
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
# PROMPT_G9 — Governance merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge governance outputs and provide coverage/consistency checks.

OUTPUTS:
  • GOV_MERGED.json
  • GOV_QA.json

RULES:
  • Sort arrays stably and remove duplicates.
```
