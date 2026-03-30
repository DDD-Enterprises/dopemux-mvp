# PROMPT_A9

## Goal
Produce `A9` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- `REPO_TASKX_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_IMPLICIT_BEHAVIOR_HINTS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_IMPLICIT_BEHAVIOR_HINTS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_IMPLICIT_BEHAVIOR_HINTS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream A-Phase artifacts (A0-A8); focus on "convention over configuration" and undocumented defaults.
2. Scan configuration loaders and "defaults" modules (e.g., `src/dopemux/config/defaults.py`, `config/settings.yaml`) for:
   - `config search order`: identify the sequence of paths checked for environment or config files (e.g., `./.env`, `~/.dopemux/env`).
   - `default paths`: identify hardcoded fallbacks for log files, databases, or cache directories.
3. Scan for "if-file-exists" behaviors: identify logic that triggers automatically based on the presence of marker files like `.dopetask-pin`, `.git`, or `.mcp-proxy-config.local`.
4. Identify "silent" operational behaviors:
   - `fallback_chains`: identify models or servers swapped automatically without explicit user configuration.
   - `auto_migrations`: search for scripts or decorators that run schema updates on service startup.
5. Extract environment variable toggles: identify `env` keys that enable hidden or implicit modes (e.g., `DEBUG_MODE`, `SKIP_VALIDATION`, `OFFLINE_ONLY`).
6. Build relationship graph: link implicit behaviors to the files or environment conditions that trigger them.
7. For each IMPLICIT_BEHAVIOR_HINTS item, populate `id` (hint:<stable_id>), description, risk, and `evidence`.
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
# PROMPT: A9 - Repo Implicit Behavior Hints

Phase: A
Step: A9

Outputs:
- REPO_IMPLICIT_BEHAVIOR_HINTS.json

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
  "artifact": "REPO_IMPLICIT_BEHAVIOR_HINTS.json",
  "phase": "A",
  "step": "A9",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "hint:<stable_id>",
      "hint_type": "...",
      "description": "...",
      "toggle_or_path": "...",
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
- Explicitly documented implicit behavior: config search order, default paths, if-file-exists toggles, env-var toggles, hidden coupling points when directly stated
```
