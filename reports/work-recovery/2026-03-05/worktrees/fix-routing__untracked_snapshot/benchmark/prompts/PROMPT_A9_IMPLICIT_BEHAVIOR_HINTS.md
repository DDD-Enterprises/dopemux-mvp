# PROMPT_A9

## Goal
Produce `A9` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
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
1. Load all upstream A-Phase artifacts (A0-A8); use the full repo control inventory as the scan surface for implicit behavior discovery.
2. Scan instruction files and configuration for implicit behavioral expectations: conventions not explicitly stated as rules but implied by file organization, naming patterns, or undocumented configuration defaults.
3. Identify implicit dependencies: locate patterns where one component assumes another is running, assumes a specific environment variable is set, or assumes a particular directory structure without explicit documentation.
4. Extract undocumented conventions: naming patterns (e.g., `*_test.py`, `__init__.py` exports), directory semantics (e.g., `scripts/` vs `tools/`), and assumed tool availability (e.g., `make`, `docker`, `tmux`).
5. For each REPO_IMPLICIT_BEHAVIOR_HINTS item, populate `id` using `REPO_IMPLICIT_BEHAVIOR_HINTS:<stable-hash(path|symbol|name)>`, `component`, `symbol`, `path`, `line_range`, and `evidence`.
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
- Speculation risk: if an implicit behavior cannot be distinguished from coincidence without additional context, emit with `confidence: low` and `status: speculative` citing the limited evidence.
- Explicit-implicit overlap: if an implicit behavior is also documented explicitly elsewhere, cross-reference the explicit documentation and emit with `status: partially_documented`.

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
