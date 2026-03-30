# PROMPT_A6

## Goal
Produce `A6` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_COMPOSE_SERVICE_GRAPH.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_COMPOSE_SERVICE_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_COMPOSE_SERVICE_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the compose service graph partition.
2. Scan `compose.yml`, `docker-compose*.yml`, and `compose/*.yml` for service definitions and architecture maps.
3. For each service block found under `services:`, extract mandatory implementation facts:
   - `service_name`: the top-level service key.
   - `image` or `build`: extract the literal image tag or the local Dockerfile/context path.
   - `env`: list environment variable keys defined in `environment` or referenced in `env_file`.
   - `ports`: extract literal port mappings (e.g., "8080:80").
   - `volumes`: list source/target mount points and named volume references.
   - `depends_on`: capture explicit service dependencies and healthcheck requirements.
   - `networks`: list network aliases and driver types.
4. Identify top-level infrastructure definitions:
   - `networks`: scan for global network configurations and external flags.
   - `volumes`: scan for global volume drivers and local paths.
5. Build relationship graph: map services as `nodes` and `depends_on` or `network` links as `edges`.
6. For each COMPOSE_SERVICE_GRAPH item, populate `id` (service:<name>), required fields, and `evidence`.
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
# PROMPT: A6 - Compose Service Graph

Phase: A
Step: A6

Outputs:
- REPO_COMPOSE_SERVICE_GRAPH.json

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
  "artifact": "REPO_COMPOSE_SERVICE_GRAPH.json",
  "phase": "A",
  "step": "A6",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "service:<name>",
      "service_name": "...",
      "image": "...",
      "build": "...",
      "env": ["..."],
      "ports": ["..."],
      "volumes": ["..."],
      "depends_on": ["..."],
      "networks": ["..."],
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
- Compose services: image/build, env names, volumes, ports, depends_on
- Networks and volumes
- Do not infer service meaning unless explicitly named
```
