# PROMPT_A7

## Goal
Produce `A7` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- `REPO_ROUTER_SURFACE.json`
- `REPO_HOOKS_SURFACE.json`
- `REPO_COMPOSE_SERVICE_GRAPH.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_LITELLM_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_LITELLM_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_LITELLM_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on LiteLLM configuration surfaces.
2. Scan `litellm.config`, `config/litellm/*.yaml`, and `src/dopemux/router/litellm_proxy.py` for model and provider declarations.
3. For each LiteLLM configuration entry, extract mandatory facts:
   - `provider`: identify the target LLM provider (e.g., "openai", "anthropic", "vertex_ai").
   - `model`: extract the literal model string or alias (e.g., "gpt-4-turbo", "claude-3-opus").
   - `env_var_requirements`: list specific environment variable names (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
   - `budgets` and `rate_limits`: identify `max_budget`, `max_parallel_requests`, `rpm`, or `tpm` constraints.
   - `cache_settings`: identify cache type (redis, in-memory) and TTL if defined.
   - `logging_or_db`: identify `success_callback`, `failure_callback`, or `database_url` for telemetry.
4. Identify any explicit "proxy" or "server" endpoints defined in the LiteLLM config or compose files.
5. Build relationship graph: link models to their respective providers and environment variable requirements.
6. For each LITELLM_SURFACE item, populate `id` (litellm:<stable_id>), required fields, and `evidence`.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path|symbol|name).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID.
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A7 - Repo LiteLLM Surface

Phase: A
Step: A7

Outputs:
- REPO_LITELLM_SURFACE.json

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
  "artifact": "REPO_LITELLM_SURFACE.json",
  "phase": "A",
  "step": "A7",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "litellm:<stable_id>",
      "config_file": "...",
      "provider": "...",
      "model": "...",
      "env_var_requirements": ["..."],
      "budgets": ["..."],
      "rate_limits": ["..."],
      "cache_settings": ["..."],
      "logging_or_db": ["..."],
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
- LiteLLM config files/references, model/provider declarations
- Expected env var names only, budgets/rate limits/cache/logging/db settings if present
```
