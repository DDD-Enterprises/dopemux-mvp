# PROMPT_A3

## Goal
Produce `A3` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_MCP_PROXY_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_MCP_PROXY_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_MCP_PROXY_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the MCP proxy partition.
2. Scan `mcp-proxy-config.yaml`, `mcp-proxy-config.copilot.yaml`, and `configs/proxy/*.json` for proxy definitions.
3. Identify proxy endpoints: scan for `endpoint`, `url`, `listen`, `port`, or `host` fields.
4. Extract upstream targets and routing rules:
   - `upstream_targets`: search for `upstreams`, `targets`, `backends`, or `proxy_pass` blocks.
   - `routes`: identify path-to-server mappings (e.g., `/mcp/google-search` -> `google-search-server`).
5. Identify authentication and security handling:
   - `auth_method`: scan for `auth`, `api_key`, `bearer`, `token`, or `headers` keys.
6. Record routing logic: scan for explicit "search order", "fallback", or "retry" logic in the proxy config.
7. Build relationship graph: trace the flow from proxy endpoint to upstream MCP server targets.
8. For each REPO_MCP_PROXY_SURFACE item, populate `id` (mcp-proxy:<name_or_path>), required fields, and `evidence`.
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
# PROMPT: A3 - MCP Proxy Surface

Phase: A
Step: A3

Outputs:
- REPO_MCP_PROXY_SURFACE.json

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
  "artifact": "REPO_MCP_PROXY_SURFACE.json",
  "phase": "A",
  "step": "A3",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "mcp-proxy:<name_or_path>",
      "proxy_name": "...",
      "endpoint": "...",
      "upstream_targets": ["..."],
      "routes": ["..."],
      "auth_method": "...",
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
- Proxy config between clients/Dopemux and MCP servers
- Endpoints, routing rules, upstream targets, auth handling (only if explicit)
- Config search order hints only if explicit
```
