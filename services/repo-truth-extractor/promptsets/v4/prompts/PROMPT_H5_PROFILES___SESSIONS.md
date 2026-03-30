# PROMPT_H5

## Goal
Produce `H5` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`
- `HOME_MCP_SURFACE.json`
- `HOME_ROUTER_SURFACE.json`
- `HOME_PROVIDER_LADDER_HINTS.json`
- `HOME_LITELLM_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_PROFILES_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_PROFILES_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_PROFILES_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the profiles and sessions partition as primary scan surface
2. Extract profiles and sessions facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted profiles and sessions elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each HOME_PROFILES_SURFACE item, populate `id`, required fields, and `evidence`
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
# Phase H5: Home Profiles + Sessions Surface

Goal:
- Extract any operator profiles, session presets, persona configs, or “profile selection” hints from home control-plane.

Outputs:
- HOME_PROFILES_SURFACE.json

HOME_PROFILES_SURFACE.json:
{
  "surface_version": "H5.v1",
  "generated_at": "<iso8601>",
  "profiles": [
    {
      "name": "<string>",
      "path": "<path>",
      "fields": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes": "<string>"
    }
  ],
  "notes":[]
}
```
