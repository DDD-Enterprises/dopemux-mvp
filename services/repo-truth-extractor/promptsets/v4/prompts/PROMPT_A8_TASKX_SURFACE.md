# PROMPT_A8

## Goal
Produce `A8` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- `REPO_LITELLM_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_TASKX_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_TASKX_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_TASKX_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on TaskX configuration and invocation surfaces.
2. Scan `.taskx/`, `task-packets/`, and `config/taskx/*.yaml` for TaskX metadata and packet definitions.
3. Identify TaskX invocations in scripts and workflows:
   - Search for literal command strings: `taskx run`, `taskx-cli`, or `python -m taskx`.
4. Extract concrete implementation facts:
   - `packet_path`: locate where task packets (CSV, JSON, YAML) are stored or generated.
   - `instruction_surfaces`: identify files or directories used for task-specific "custom instructions" or "prompts".
   - `operator_surface`: identify "operator profiles" or "agent definitions" used during execution.
5. Trace connections between task packets, the instructions they reference, and the operators invoked to process them.
6. Build relationship graph: map the flow from a task trigger to the final packet output.
7. For each TASKX_SURFACE item, populate `id` (taskx:<stable_id>), required fields, and `evidence`.
8. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
9. Build deterministic IDs using stable content keys (path|symbol|name).
10. Attach evidence to every non-derived field and every relationship edge.
11. Normalize arrays by stable sort keys; deduplicate by ID.
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
13. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A8 - Repo TaskX Surface

Phase: A
Step: A8

Outputs:
- REPO_TASKX_SURFACE.json

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
  "artifact": "REPO_TASKX_SURFACE.json",
  "phase": "A",
  "step": "A8",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "taskx:<stable_id>",
      "invocation": "...",
      "config_file": "...",
      "packet_path": "...",
      "operator_surface": "...",
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
- .taskx files, taskx config, scripts/workflows invoking taskx
- Packet paths, instruction compilation/injection surfaces, operator profile surfaces
```
