# PROMPT_M5

## Goal
Produce `M5` outputs for phase `M` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/**`
- `docker/**`
- `extraction/**`
- Upstream normalized artifacts available to this step:
- `M0_RUNTIME_EXPORT_INVENTORY.json`
- `M1_SQLITE_SCHEMA_SNAPSHOTS.json`
- `M2_SQLITE_TABLE_COUNTS.json`
- `M3_CONPORT_EXPORT_SAFE.json`
- `M4_DOPE_CONTEXT_EXPORT_SAFE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `M5_MCP_HEALTH_EXPORT_SAFE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `M5_MCP_HEALTH_EXPORT_SAFE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `M5`
    - `id_rule`: `M5_MCP_HEALTH_EXPORT_SAFE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. For each MCP server definition discovered in H-phase (`HOME_MCP_SURFACE.json`), extract a health summary without making network calls: server name, command path, argument count, environment variable key names (never values), and config file presence/parseability.
2. Check each MCP server command for local file existence: does the command binary exist at the specified path? Is the referenced config file present and parseable (valid JSON/YAML)? Record results with evidence.
3. Classify each MCP server health status: `config_valid` (all referenced files present and parseable), `config_incomplete` (some references missing), or `config_invalid` (parse errors detected).
4. Cross-reference against upstream `REPO_MCP_SERVER_DEFS.json` to identify home-level overrides of repo-defined MCP servers.
5. Legacy Context is intent guidance only and is never evidence.
6. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
7. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
8. Attach evidence to every non-derived field and every relationship edge.
9. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
10. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
11. Emit exactly the declared outputs and no additional files.

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
- Do not invent endpoints, handlers, dependencies, env vars, commands, or policy claims.
- Do not infer intent from filenames alone; require direct textual/code evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- MCP server command references an absolute path that does not exist: emit with `status: command_not_found` and the path as evidence.
- MCP server config file contains syntax errors: emit with `status: parse_error` and the error message as evidence (redact any secret-like values).

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: M5_MCP_HEALTH_EXPORT_SAFE.json

Prompt:
- Task: export MCP health summary without network calls.
- Include:
  - MCP server definitions (name, command, args count)
  - env keys only (never env values)
  - file/config presence checks and parseability status
  - implementer metadata: implementer="GPT-5.3-Codex", authority="Codex CLI/Desktop"
- Hard rules:
  - Do not perform network probes.
  - Do not expose secrets or values.
  - Keep output bounded; include truncation markers when capped.
```
