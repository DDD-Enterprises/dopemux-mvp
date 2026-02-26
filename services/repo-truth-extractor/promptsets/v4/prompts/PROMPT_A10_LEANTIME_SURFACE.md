# PROMPT_A10

## Goal
Produce `A10` outputs for phase `A` by extracting the repository control-plane surfaces that configure or route Leantime integration behavior.
Capture only implementation facts that are directly evidenced in source and configuration files.

## Inputs
- Source scope (scan these roots first):
  - `services/leantime-bridge/**`
  - `config/**`
  - `compose.yml`
  - `docker-compose*.yml`
  - `src/dopemux/**`
  - `.claude.json`
  - `README.md`
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
1. Enumerate Leantime-related files and symbols from in-scope paths.
2. Extract concrete control-plane facts (ports, env vars, command wiring, enable flags).
3. Build deterministic IDs from stable `(path, symbol/name, key)`.
4. Attach evidence to every non-derived field and integration relation.
5. Normalize with stable sorting and deterministic deduplication.
6. Emit exactly the declared output file.

## Evidence Rules
- Every load-bearing value must include at least one evidence object:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- `path` must be repo-relative.
- `excerpt` must be exact and <= 200 chars.
- If evidence is missing, keep field as `UNKNOWN` with `missing_evidence_reason`.

## Determinism Rules
- Norm output MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort items by `(path, line_start, id)` when available, otherwise by `id`.
- Deduplicate by `id`; merge evidence by unique `(path,line_range,excerpt)`.
- For scalar conflicts choose non-empty value, else lexicographically smallest stable value.

## Anti-Fabrication Rules
- Do not invent Leantime endpoints, credentials, commands, or bridge behavior.
- Do not infer configuration support from filenames alone; require direct text/code evidence.
- Do not copy QA metadata into norm output.
- Keep unresolved values as `UNKNOWN`; never substitute guesses.

## Failure Modes
- Missing files: emit valid empty `ItemList` and include `missing_inputs` notes in items.
- Ambiguous or conflicting config: emit candidates with `status: needs_review` and evidence.
- Partial scan: emit partial output with explicit `coverage_notes` and evidence gaps.
- Parse failures: keep deterministic partial output and capture `parse_error` in item notes.

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
