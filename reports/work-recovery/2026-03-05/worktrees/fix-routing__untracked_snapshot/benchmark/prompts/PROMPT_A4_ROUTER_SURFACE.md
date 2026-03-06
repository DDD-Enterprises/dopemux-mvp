# PROMPT_A4

## Goal
Produce `A4` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `.claude/**`
- `.github/**`
- `.taskx/**`
- `config/**`
- `scripts/**`
- `docker/**`
- `compose.yml`
- `docker-compose*.yml`
- `README.md`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `REPOCTRL_INVENTORY.json`
- `REPOCTRL_PARTITIONS.json`
- `REPO_INSTRUCTION_SURFACE.json`
- `REPO_INSTRUCTION_REFERENCES.json`
- `REPO_MCP_SERVER_DEFS.json`
- `REPO_MCP_PROXY_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_ROUTER_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_ROUTER_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_ROUTER_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream artifacts including `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; scan for routing configuration files (`routing.yaml`, `templates/routing.yaml`, any `*routing*` config files).
2. Extract all model routing definitions: slot names, model aliases, provider ladders (primary/fallback chains), temperature/parameter overrides, and context window limits; record exact YAML/JSON paths and line ranges.
3. Identify routing decision logic in code: locate any Python/JS modules that parse routing configs, apply model selection, or implement fallback chains; extract the routing algorithm with file:line evidence.
4. Map routing aliases to concrete model identifiers: trace each alias through the config chain to the final provider+model pair; record all intermediate mappings.
5. For each REPO_ROUTER_SURFACE item, populate `id` using `REPO_ROUTER_SURFACE:<stable-hash(path|symbol|name)>`, `component`, `symbol`, `path`, `line_range`, and `evidence`.
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
- Alias without resolution: if a routing alias cannot be resolved to a concrete model through static config analysis, emit with `resolved_model: UNKNOWN` and evidence of the unresolvable alias.
- Stale routing config: if a routing config references a model or provider not available in any environment variable or secrets config, emit with `status: potentially_stale` and `coverage_notes`.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A4 - Repo Router Surface

Phase: A
Step: A4

Outputs:
- REPO_ROUTER_SURFACE.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_ROUTER_SURFACE.json",
  "phase": "A",
  "step": "A4",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "route:<stable_id>",
      "provider": "...",
      "model": "...",
      "trigger": "...",
      "fallback_ladder": ["..."],
      "retry_policy": "...",
      "rate_limit_policy": "...",
      "profile": "...",
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- Provider/model routing tables, fallback ladders, profiles, routing rules
- Any retry/backoff/rate-limit knobs if present
- Routing policy files if present
```
