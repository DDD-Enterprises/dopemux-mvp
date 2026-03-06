# PROMPT_H4

## Goal
Produce `H4` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_LITELLM_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_LITELLM_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_LITELLM_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `HOME_INVENTORY.json` and `HOME_PARTITIONS.json`; use the LiteLLM partition as the primary scan surface.
2. Extract LiteLLM config references from home files: scan for `litellm_config.yaml`, proxy configs, and environment variables with `LITELLM_*` prefix; record config paths and key settings.
3. Identify spend/log database hints: locate LiteLLM spend tracking DB paths, log file locations, and proxy analytics configuration.
4. Extract provider entries: for each LiteLLM model/provider entry, record model name, provider, API base, and any budget or rate limit settings.
5. For each HOME_LITELLM_SURFACE item, populate `id`, required fields, and `evidence`.
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
- Spend DB without schema: if a LiteLLM spend DB is referenced but its schema cannot be determined, emit with `schema: UNKNOWN` and `missing_evidence_reason`.
- Duplicate provider entries: if the same provider+model appears in both home and repo LiteLLM configs, emit both with `status: duplicate_provider` and evidence.

## Legacy Context (for intent only; never as evidence)
```markdown
# Phase H4: Home LiteLLM Surface

Goal:
- Extract LiteLLM config references, proxy configs, spend/log DB hints, and provider entries from home control-plane.

Outputs:
- HOME_LITELLM_SURFACE.json

HOME_LITELLM_SURFACE.json:
{
  "surface_version": "H4.v1",
  "generated_at": "<iso8601>",
  "configs": [
    {
      "path": "<path>",
      "providers": ["<string>"],
      "models": ["<string>"],
      "db_or_logs": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}
```
