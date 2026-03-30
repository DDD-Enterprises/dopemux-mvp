# PROMPT_A11

## Goal
Produce `A11` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Extract editor and IDE integration surfaces: configuration files, settings, extensions, and workspace definitions that control how code editors (VS Code, Cursor, Claude Code, Copilot) interact with the repository.

## Inputs
- Source scope (scan these roots first):
  - `.vibe/**`
  - `.claude/**`
  - `.dopemux/**`
  - `.github/**`
  - `.githooks/**`
  - `.taskx/**`
  - `mcp-proxy-config.copilot.yaml`
  - `mcp-proxy-config*.yaml`
  - `mcp-proxy-config.json`
  - `compose/**`
  - `config/**`
  - `configs/**`
  - `docker/**`
  - `installers/**`
  - `ops/**`
  - `scripts/**`
  - `tools/**`
  - `src/dopemux/claude/**`
  - `.vscode/**`
  - `.cursor/**`
  - `.editorconfig`
  - `*.code-workspace`
- Upstream normalized artifacts available to this step:
  - `REPOCTRL_INVENTORY.json`
  - `REPOCTRL_PARTITIONS.json`
  - `REPO_INSTRUCTION_SURFACE.json`
  - `REPO_MCP_SERVER_DEFS.json`
  - `REPO_MCP_PROXY_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `EDITOR_INTEGRATION_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `EDITOR_INTEGRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A11`
    - `id_rule`: `EDITOR_INTEGRATION_SURFACE:<stable-hash(path|editor_type|config_key)>`
    - `required_item_fields`: `id, editor_type, config_key, config_value, scope, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
- `editor_type` enum: `vscode | cursor | claude_code | copilot | editorconfig | workspace | other`
- `scope` enum: `workspace | user | project | global`

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on editor and IDE integration surfaces.
2. Scan `.vscode/settings.json`, `.vscode/extensions.json`, and `.cursor/rules/` for editor-specific behaviors and constraints.
3. Scan `mcp-proxy-config*.yaml` and `mcp-proxy-config.json` for editor-facing MCP proxy configurations and tool bindings.
4. Extract Claude Code configuration facts: scan `.claude/config.json` and `claude_desktop_config.json` for tool registrations and agent profiles.
5. Identify Copilot instruction sets: scan `.github/copilot-instructions.md` and related YAML metadata for repository-wide AI guidance.
6. Parse `.editorconfig` for formatting contracts and `*.code-workspace` files for multi-root project definitions.
7. For each integration point, extract mandatory fields:
   - `editor_type`: categorize as `vscode`, `cursor`, `claude_code`, `copilot`, or `editorconfig`.
   - `config_key` and `config_value`: capture literal setting pairs (e.g., `"editor.formatOnSave": true`).
   - `scope`: classify as `workspace` (in-repo) or `project`.
8. Cross-reference with `REPO_MCP_SERVER_DEFS.json` to identify which MCP tools are explicitly bound to which editor interface.
9. For each EDITOR_INTEGRATION_SURFACE item, populate `id`, required fields, and `evidence`.
10. Build deterministic IDs using stable content keys (path|editor_type|config_key).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID.
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
