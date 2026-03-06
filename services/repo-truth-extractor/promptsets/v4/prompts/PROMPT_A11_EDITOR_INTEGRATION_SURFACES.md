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
1. Load upstream inventory and partitions; use the editor/IDE partition as primary scan surface
2. Scan `.vibe/`, `.claude/`, `.cursor/`, `.vscode/` directories for editor-specific configuration files
3. Extract MCP proxy configurations from `mcp-proxy-config*.yaml` and `mcp-proxy-config.json`
4. Identify Claude Code settings: `claude_desktop_config.json`, `claude.json`, `.claude/` directory structures
5. Extract Copilot integration points: copilot-related YAML configs, GitHub Copilot settings
6. Parse `.editorconfig` and `*.code-workspace` files for workspace-level settings
7. For each integration point, classify `editor_type`, `scope`, and extract `config_key`/`config_value` pairs
8. Cross-reference with `REPO_MCP_SERVER_DEFS.json` and `REPO_MCP_PROXY_SURFACE.json` to identify MCP-editor bindings
9. Build deterministic IDs using stable content keys (path/editor_type/config_key)
10. Attach evidence to every non-derived field and every relationship edge
11. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash)
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps
13. Emit exactly the declared outputs and no additional files

## Evidence Rules
- Every load-bearing value must carry at least one evidence object:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- `path` must be repo-relative (never absolute in norm artifacts).
- `excerpt` must be exact (no paraphrase) and <= 200 chars.
- If the source is ambiguous, include multiple evidence objects and set value to `UNKNOWN`.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent editor settings, extensions, config keys, or integration points.
- Do not infer intent from filenames alone; require direct textual/code evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.
- Do not assume an editor is integrated because a config directory exists; verify actual config content.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Unrecognized editor config format: emit item with `editor_type: other` and raw content evidence.
- Multiple editors sharing same MCP proxy: emit separate items per editor binding with cross-reference evidence.
