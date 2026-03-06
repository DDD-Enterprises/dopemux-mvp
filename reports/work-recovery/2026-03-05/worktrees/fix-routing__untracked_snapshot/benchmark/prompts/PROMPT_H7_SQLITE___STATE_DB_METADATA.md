# PROMPT_H7

## Goal
Produce `H7` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`
- `HOME_KEYS_SURFACE.json`
- `HOME_REFERENCES.json`
- `HOME_MCP_SURFACE.json`
- `HOME_ROUTER_SURFACE.json`
- `HOME_PROVIDER_LADDER_HINTS.json`
- `HOME_LITELLM_SURFACE.json`
- `HOME_PROFILES_SURFACE.json`
- `HOME_TMUX_WORKFLOW_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_SQLITE_SCHEMA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_SQLITE_SCHEMA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H9`
    - `id_rule`: `HOME_SQLITE_SCHEMA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `HOME_INVENTORY.json` and `HOME_PARTITIONS.json`; use the state DB partition as the primary scan surface.
2. Detect SQLite DB references: scan home config files for `.db`, `.sqlite`, `.sqlite3` path references; for each, record the path, purpose (spend tracking, state persistence, logging), and owning tool.
3. Identify schema files and migrations: locate SQL schema definitions, migration scripts, or ORM model files that correspond to detected databases; extract table definitions with column types.
4. Extract state directory references: identify directories used for persistent state (`~/.local/share/`, cache dirs, custom state paths); record the directory, contents pattern, and owning tool.
5. For each HOME_SQLITE_SCHEMA item, populate `id`, DB path, tables, schema details, and `evidence`.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

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
- DB without schema definition: if a SQLite DB path is referenced but no schema file or migration exists, emit with `schema: UNKNOWN` and `missing_evidence_reason`.
- Runtime-only DB: if a database is created only at runtime with no static schema, emit with `status: runtime_created` and evidence of the creation code.

## Legacy Context (for intent only; never as evidence)
```markdown
# Phase H7: Home SQLite + State DB Metadata

Goal:
- Detect references to sqlite DB files, schema files, migrations, or state directories in home control plane configs.
- If you have actual sqlite schema text in context, extract table/index names as metadata only (no secret contents).

Outputs:
- HOME_SQLITE_SCHEMA.json

HOME_SQLITE_SCHEMA.json:
{
  "surface_version": "H7.v1",
  "generated_at": "<iso8601>",
  "db_files": [
    {
      "path": "<path>",
      "evidence": {"path":"<path>","line_range":"Lx-Ly","snippet":"<redacted snippet>"},
      "notes":"<string>"
    }
  ],
  "schema_hints": [
    {
      "source_path": "<path>",
      "tables": ["<string>"],
      "indexes": ["<string>"],
      "triggers": ["<string>"],
      "evidence": {"line_range":"Lx-Ly","snippet":"<redacted snippet>"}
    }
  ],
  "notes":[]
}
```
