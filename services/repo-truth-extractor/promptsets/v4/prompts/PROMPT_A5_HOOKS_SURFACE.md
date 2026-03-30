# PROMPT_A5

## Goal
Produce `A5` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- `src/dopemux/hooks/**`
- `src/dopemux/mcp/hooks.py`

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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_HOOKS_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_HOOKS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_HOOKS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the hooks partition.
2. Scan `.githooks/`, `.github/workflows/`, and `.pre-commit-config.yaml` for external hook triggers.
3. Scan `src/dopemux/hooks/**` and `src/dopemux/mcp/hooks.py` for internal hook registrations and decorators.
4. For each hook identified, extract mandatory fields:
   - `hook_type`: categorize as "git-hook", "pre-commit", "ci-pipeline", "task-hook", or "mcp-hook".
   - `trigger`: identify the triggering event (e.g., `git commit`, `cron`, `workflow_dispatch`, `on_task_start`).
   - `command`: extract the literal shell command string or python function name invoked.
   - `invoked_paths`: list file patterns the hook watches or modifies (e.g., `*.py`, `docs/**`).
5. Build relationship graph: link hooks to the files they monitor and the commands they execute.
6. For each HOOKS_SURFACE item, populate `id` (hook:<type>:<name>), required fields, and `evidence`.
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
# PROMPT: A5 - Repo Hooks Surface

Phase: A
Step: A5

Outputs:
- REPO_HOOKS_SURFACE.json

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
  "artifact": "REPO_HOOKS_SURFACE.json",
  "phase": "A",
  "step": "A5",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "hook:<type>:<name>",
      "hook_type": "...",
      "trigger": "...",
      "command": "...",
      "invoked_paths": ["..."],
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
- Git hooks, pre-commit hooks, CI hooks, taskx/dopemux hooks
- Literal commands invoked, source file locations, triggering conditions if defined
```
