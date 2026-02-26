# PROMPT_A1

## Goal
Produce `A1` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_INSTRUCTION_SURFACE.json`
- `REPO_INSTRUCTION_REFERENCES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_INSTRUCTION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_INSTRUCTION_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `REPO_INSTRUCTION_REFERENCES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_INSTRUCTION_REFERENCES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Use REPOCTRL_PARTITIONS.json (A0 upstream) to find the instructions/prompts partition items.
2. For each candidate path, verify it exists within the source scope roots before processing.
3. Classify each instruction file kind using direct textual markers in file content:
   - claude_system, agent_profile, tooling_instructions, prompt_template, workflow_playbook, other
   Attach evidence for the marker used (path, line_range, excerpt <=200 chars).
4. Extract declared behaviors, boundaries, and dataflows as literal statements from the file.
   Record each statement with evidence (path, line_range, excerpt <=200 chars).
5. Scan instruction files for literal references to:
   - services (conport, serena, dope-context, dashboard, orchestrator, proxy)
   - MCP servers/tools
   - router/provider ladders
   - scripts/commands
   Record each mention with evidence (path, line_range, excerpt <=200 chars).
6. Build REPO_INSTRUCTION_REFERENCES.json by linking each mention back to its source file and
   forward to the referenced target when the target string is literal and unambiguous.
   If the target cannot be resolved, keep target as UNKNOWN and include evidence of ambiguity.
7. Determine scope only when explicitly declared in file content (e.g., "repo-wide",
   "project-specific", "tool-specific"). If not explicitly declared, set scope to UNKNOWN.
8. Legacy Context is intent guidance only and is never evidence.
9. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
10. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
11. Attach evidence to every non-derived field and every relationship edge.
12. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
13. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
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
- Upstream A0 partitions missing or empty for instructions/prompts: emit valid empty containers
  with missing_inputs referencing the absent upstream artifact; skip instruction extraction.
- Truncated or malformed instruction sources (e.g., incomplete markdown fences): record the item
  with available evidence and mark missing fields as UNKNOWN with missing_evidence_reason:
  "source content truncated".

## Legacy Context (for intent only; never as evidence)
```markdown
# PHASE A1 — INSTRUCTION SURFACES (REPO)
Model: Gemini Flash 3
Goal: Produce REPO_INSTRUCTION_SURFACE.json + REPO_INSTRUCTION_REFERENCES.json

Hard rules:
- Extract ONLY what is explicitly present in files.
- Every extracted item MUST include evidence: {path, anchor_excerpt<=200 chars}.
- No guessing. If unclear, record UNKNOWN with evidence showing ambiguity.

Inputs:
- Partition content from A0 P0 partitions: instruction docs, agent files, custom instructions directories.

Task:
1) Build REPO_INSTRUCTION_SURFACE.json:
   Identify all instruction-bearing files and normalize into:
   - instruction_sources[] items:
     - id (stable, e.g., INSTR_0001)
     - path
     - kind (one of: "claude_system", "agent_profile", "tooling_instructions", "prompt_template", "workflow_playbook", "other")
     - scope (repo-wide / project-specific / tool-specific)
     - referenced_tools (list of strings found literally: e.g., "conport", "serena", "mcp", "litellm", "taskx")
     - declared_behaviors (list of short literal statements, each with anchor_excerpt)
     - declared_boundaries (list, each with anchor_excerpt)
     - declared_dataflows (list, each with anchor_excerpt)
   Determinism: sort by path, then by first appearance.

2) Build REPO_INSTRUCTION_REFERENCES.json:
   A cross-reference map of “instruction mentions -> targets”.
   Extract literal references to:
   - services (conport, serena, dope-context, dashboard, orchestrator, proxy)
   - MCP servers/tools
   - router/provider ladders
   - scripts/commands
   Output:
   - references[]:
     - ref_type ("service"|"command"|"file_p
```
