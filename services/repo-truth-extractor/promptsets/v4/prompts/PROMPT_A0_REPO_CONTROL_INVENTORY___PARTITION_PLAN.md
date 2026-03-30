# PROMPT_A0

## Goal
Produce `A0` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- `components/**`
- `contracts/**`
- `dashboard/**`
- `docs/**`
- `examples/**`
- `installers/**`
- `interruption_shield/**`
- `ops/**`
- `plugins/**`
- `profiles/**`
- `review_artifacts/**`
- `services/**`
- `shared/**`
- `src/**`
- `SYSTEM_ARCHIVE/**`
- `task-packets/**`
- `templates/**`
- `tests/**`
- `ui-dashboard/**`
- `ui-dashboard-backend/**`
- `UPGRADES/**`
- `vendor/**`


- `extraction/**`
- `reports/**`




- `compose.yml`
- `docker-compose*.yml`
- `README.md`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPOCTRL_INVENTORY.json`
- `REPOCTRL_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPOCTRL_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A0`
    - `id_rule`: `REPOCTRL_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPOCTRL_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A0`
    - `id_rule`: `REPOCTRL_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan repo control-plane (`*.yaml`, `*.toml`, `*.json`, `docker-compose*`, `.claude/`) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the repo control-plane (`*.yaml`, `*.toml`, `*.json`, `docker-compose*`, `.claude/`) domain
3. Build REPO_CTRL_PARTITIONS by grouping files into logical categories with rationale
4. For each REPO_CTRL_INVENTORY item, populate `id`, `path`, `kind`, `summary`, and `evidence`
5. For each REPO_CTRL_PARTITIONS item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
MODE: Mechanical extractor, zero interpretation.
INPUT: repo working tree (top-level), include hidden dirs shown in ls -la (not .git contents).
OUTPUT:
- REPOCTRL_INVENTORY.json: list files (path, ext, size, mtime, sha256 if available), plus first 30 non-empty lines for text.
- REPOCTRL_PARTITIONS.json: partitions by type:
  - instructions/prompts (CLAUDE.md, AGENTS.md, .claude/**, docs/** instruction files)
  - mcp/proxy configs (mcp-proxy-config*, start-mcp-servers.sh, compose/**)
  - hooks (.githooks/**, scripts called by hooks)
  - routers/provider ladders (litellm.config*, any router yaml/toml/json)
  - compose/service graphs (compose.yml, docker-compose*.yml, compose/**)
  - CI/gates (.github/**, pre-commit, ruff/mypy/pytest configs)
  - taskx surfaces (.taskx/**, .taskx-pin, task packets in repo)
RULES: JSON only. Every item must include path + line_range (or null if binary).
```
