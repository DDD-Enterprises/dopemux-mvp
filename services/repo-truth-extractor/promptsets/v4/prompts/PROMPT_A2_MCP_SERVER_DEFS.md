# PROMPT_A2

## Goal
Produce `A2` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `.claude/**`
- `.github/**`
- `.taskx/**`
- `config/**`
- `scripts/**`
- `docker/**`
- `compose.yml`
- `docker-compose*.yml`
- `README.md`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `REPOCTRL_INVENTORY.json`
- `REPOCTRL_PARTITIONS.json`
- `REPO_INSTRUCTION_SURFACE.json`
- `REPO_INSTRUCTION_REFERENCES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_MCP_SERVER_DEFS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_MCP_SERVER_DEFS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_MCP_SERVER_DEFS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Locate MCP server definition sources within the scan roots:
   - .claude/**, config/**, scripts/**, docker/**, README.md, AGENTS.md
   Include .github/** and .taskx/** only if they contain explicit MCP server blocks.
2. Identify MCP server definitions only when explicitly structured in text:
   - JSON/YAML/TOML keys like "mcp", "mcpServers", "servers", "transport"
   - CLI invocations like "claude mcp add ..." or equivalent explicit add commands
   Do not infer "MCP server" from filenames alone.
3. For each server definition, extract only explicitly evidenced fields:
   - server_name (or name/id), command, args, enabled/disabled
   - env var NAMES only (never values)
   - transport/url only if explicitly present
   If a field is referenced but not defined, set it to UNKNOWN and record why.
4. Evidence capture rule (strict):
   - For every extracted field, attach evidence with (path, line_range, excerpt <=200 chars).
   - Excerpts must be exact substrings; do not paraphrase.
5. Normalize each server into an item with the artifact's id_rule:
   - id = stable-hash(path|symbol|name) per schema
   - path must be repo-relative
   - line_range should cover the defining block or defining command line(s)
6. Deduplicate servers deterministically:
   - same stable id merges evidence by (path,line_range,excerpt)
   - if conflicting scalar values exist, prefer non-empty; else lexicographically smallest
7. Emit UNKNOWN safely:
   - If a server is mentioned but no definition exists in-scope, emit an item with UNKNOWN
     fields plus missing_evidence_reason and evidence for the mention.
8. Legacy Context is intent guidance only and is never evidence.
9. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
10. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
13. Validate required fields; emit UNKNOWN for unsatisfied values with evidence gaps.
14. Emit exactly the declared outputs and no additional files.

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
- Ambiguous MCP definition blocks (multiple plausible "name"/"command" candidates): emit item
  with UNKNOWN for ambiguous fields and include evidence for each candidate excerpt.
- Secret leakage risk (env values, tokens, inline credentials): emit env var NAMES only; if a
  value is present in the source, do not copy it into output; include evidence pointing to the
  key name only and set missing_evidence_reason: "sensitive value redacted".

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A2 - MCP Server Definitions

Phase: A
Step: A2

Outputs:
- REPO_MCP_SERVER_DEFS.json

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
  "artifact": "REPO_MCP_SERVER_DEFS.json",
  "phase": "A",
  "step": "A2",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "mcp:<name>",
      "server_name": "...",
      "command": "...",
      "args": ["..."],
      "env": ["..."],
      "enabled": true,
      "source_path": "...",
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
- MCP server definitions: name, command, args, env var names, enabled/disabled, cwd/root/allowed paths if present
- Any explicit per-server capabilities/notes
- Source locations and config keys
```
