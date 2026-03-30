# PROMPT_H1

## Goal
Produce `H1` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_KEYS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_KEYS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_REFERENCES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_REFERENCES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the keys and credential references partition as primary scan surface
2. Extract keys and credential references facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted keys and credential references elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each HOME_KEYS_SURFACE item, populate `id`, required fields, and `evidence`
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
# Phase H1: Home Keys + References Surface (Safe)

Goal:
- Extract references to environment variables, API keys, token paths, credential file paths, and configuration include-chains that appear in the provided home control-plane files.
- Do NOT output secrets. Only output key NAMES, referenced FILE PATHS, and reference locations.

Hard rules:
- Never print actual secret values.
- Prefer explicit evidence: show (path, line_range, snippet_redacted) for each reference.
- Output valid JSON only.

Outputs:
- HOME_KEYS_SURFACE.json
- HOME_REFERENCES.json

HOME_KEYS_SURFACE.json:
{
  "surface_version": "H1.v1",
  "generated_at": "<iso8601>",
  "env_vars_referenced": [
    {
      "name": "<ENV_VAR_NAME>",
      "refs": [{"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}]
    }
  ],
  "credential_paths_referenced": [
    {
      "path": "<string>",
      "refs": [{"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"}]
    }
  ],
  "notes": []
}

HOME_REFERENCES.json:
{
  "refs_version": "H1.v1",
  "generated_at": "<iso8601>",
  "includes_and_imports": [
    {
      "source_path": "<path>",
      "kind": "<include|import|source|extends|loads>",
      "target": "<string>",
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ]
}
```
