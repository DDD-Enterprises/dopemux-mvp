# PROMPT_A10

## Goal
Produce `A10` outputs for phase `A` by extracting the repository control-plane surfaces that configure or route Leantime integration behavior.
Capture only implementation facts that are directly evidenced in source and configuration files.

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

- `services/leantime-bridge/**`
- `compose.yml`
- `docker-compose*.yml`
- `src/dopemux/**`
- `.claude.json`
- `README.md`
- `installers/**`
- `ops/**`





- Upstream normalized artifacts available to this step:
  - `REPOCTRL_INVENTORY.json`
  - `REPOCTRL_PARTITIONS.json`
  - `REPO_INSTRUCTION_SURFACE.json`
  - `REPO_MCP_SERVER_DEFS.json`
  - `REPO_MCP_PROXY_SURFACE.json`
  - `REPO_ROUTER_SURFACE.json`
  - `REPO_TASKX_SURFACE.json`
  - `REPO_COMPOSE_SERVICE_GRAPH.json`
- Runner context artifacts:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
  - `services/registry.yaml`

## Outputs
- `REPO_LEANTIME_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contract:
  - `REPO_LEANTIME_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_LEANTIME_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, line_range, evidence`
- Capture these surfaces when evidenced:
  - Leantime service definitions and runtime ports
  - MCP transport wiring and endpoint URLs
  - Environment variable contracts
  - CLI command entrypoints that enable Leantime integration

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on Leantime integration surfaces.
2. Scan `services/leantime-bridge/**`, `compose.yml`, and `config/leantime/*.yaml` for service and network facts:
   - `leantime_service`: identify container name, image, and explicit `ports` (e.g., 80, 443, 8061).
   - `mcp_transport`: scan for "leantime" tools in `mcp-proxy-config.yaml` or `src/dopemux/mcp/leantime.py`.
   - `endpoint_urls`: identify literal Leantime API or webhook URLs (e.g., `LEANTIME_API_URL`).
3. Extract environment variable contracts: search for `LEANTIME_API_KEY`, `LEANTIME_DB_*`, `LEANTIME_URL`, or `LEANTIME_TOKEN`.
4. Identify CLI and workflow integration points:
   - Search for literal commands: `dopemux leantime sync`, `taskx --leantime`, or `leantime-bridge import`.
5. Build relationship graph: link the Leantime bridge service to the core Dopemux router, MCP proxy, and TaskX surfaces.
6. For each REPO_LEANTIME_SURFACE item, populate `id` (stable-hash of path|name), required fields, and `evidence`.
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
# PROMPT: A10 - Leantime Surface
Phase: A
Step: A10
Outputs:
- REPO_LEANTIME_SURFACE.json
Mode: extraction
Strict: evidence_only
```
