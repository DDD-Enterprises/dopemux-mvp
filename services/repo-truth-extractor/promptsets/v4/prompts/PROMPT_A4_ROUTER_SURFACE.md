# PROMPT_A4

## Goal
Produce `A4` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `.vibe/**`
- `.claude/**`
- `.dopemux/**`
- `.github/**`
- `.githooks/**`
- `.taskx/**`
- `mcp-proxy-config.copilot.yaml`
- `compose/**`
- `config/**`
- `configs/**`
- `docker/**`
- `scripts/**`
- `tools/**`

- `installers/**`
- `ops/**`





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
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the router partition.
2. Scan `litellm.config`, `config/router/*.yaml`, and `src/dopemux/router/**/*.py` for routing tables and model definitions.
3. Extract provider and model mappings:
   - Identify `model_list`, `routers`, or explicit model-to-provider mappings.
4. Identify routing triggers and logic:
   - `trigger`: scan for `if`, `when`, `tag`, `filter`, or `metadata` rules used for route selection.
   - `fallback_ladder`: identify `fallbacks`, `retry_models`, or sequential provider lists.
5. Extract operational policies:
   - `retry_policy`: scan for `retries`, `backoff`, or `retry_on` configuration.
   - `rate_limit_policy`: scan for `rpm`, `tpm`, `rate_limit`, or `quota` keys.
6. Identify named `profiles` (e.g., "fast-low-cost", "high-reasoning") and their associated model sets.
7. Build relationship graph: trace connections between triggers, providers, and fallback models.
8. For each ROUTER_SURFACE item, populate `id` (route:<stable_id>), required fields, and `evidence`.
9. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
10. Build deterministic IDs using stable content keys (path|symbol|name).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID.
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

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
