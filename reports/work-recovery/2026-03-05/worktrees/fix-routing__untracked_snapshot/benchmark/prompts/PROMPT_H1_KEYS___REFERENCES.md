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
1. Load upstream `HOME_INVENTORY.json` and `HOME_PARTITIONS.json`; use the keys/credentials partition as the primary scan surface.
2. Extract environment variable references: scan shell profiles, `.env` files, and config files for `export VAR=`, `${VAR}`, `os.getenv()`, and equivalent patterns; record variable name, source file, and whether a default value exists.
3. Extract credential file references: identify paths to API key files, token stores, SSH keys, and certificate files; record the path pattern and owning tool/service.
4. Build HOME_REFERENCES by tracing configuration include-chains: locate `source`, `include`, or relative path references between home config files; record the reference type and target.
5. For each HOME_KEYS_SURFACE item, populate `id`, key name, reference type, source path, and `evidence` (anchor_excerpt <= 200 chars). NEVER include actual secret values.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Evidence Rules
- Every load-bearing value must carry at least one evidence object:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- `path` must be repo-relative (never absolute in norm artifacts).
- `excerpt` must be exact (no paraphrase) and <= 200 chars.
- If the source is ambiguous, include multiple evidence objects and set value to `UNKNOWN`.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent endpoints, handlers, dependencies, env vars, commands, or policy claims.
- Do not infer intent from filenames alone; require direct textual/code evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Secret value leak: if extraction inadvertently captures a secret value, immediately replace with `REDACTED` and flag with `status: redacted_secret`.
- Broken include chain: if a config file references another config that does not exist, emit with `status: broken_include` and `missing_evidence_reason`.

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
