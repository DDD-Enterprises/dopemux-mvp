# PROMPT_H0

## Goal
Produce `H0` outputs for phase `H` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `$HOME/.claude/**`
- `$HOME/.codex/**`
- `$HOME/.taskx/**`
- `$HOME/.config/**`
- `$HOME/.tmux.conf*`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `HOME_INVENTORY.json`
- `HOME_PARTITIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `HOME_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H0`
    - `id_rule`: `HOME_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, line_range, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `HOME_PARTITIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `H0`
    - `id_rule`: `HOME_PARTITIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, partition_id, path, line_range, files, reason, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan home control-plane dirs (`~/.claude/`, `~/.config/`, shell profiles, dotfiles) targets; collect path, type, and content metadata for each artifact
2. Classify each artifact by category relevant to the home control-plane dirs (`~/.claude/`, `~/.config/`, shell profiles, dotfiles) domain
3. Build HOME_PARTITIONS by grouping files into logical categories with rationale
4. For each `HOME_INVENTORY` item, populate `id`, `path`, `line_range`, `kind`, `summary`, and `evidence`.
5. For each `HOME_PARTITIONS` item, populate `id`, `partition_id`, `path`, `line_range`, `files` (sorted), `reason`, and `evidence`.
6. Wrap all items in the `ItemList` envelope: `{"schema":"json_item_list@v1","items":[...]}`.
7. Legacy Context is intent guidance only and is never evidence.
8. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
9. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
10. Attach evidence to every non-derived field and every relationship edge.
11. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
13. Emit exactly the declared outputs and no additional files.

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
- Sensitive file: if a home file may contain secrets, reference by path only; emit with `kind: sensitive` and `content: REDACTED`
- Missing home dir: if the home scan target does not exist, emit with `status: inaccessible`

## Legacy Context (for intent only; never as evidence)
```markdown
MODE: Mechanical extractor, zero interpretation.
TASK: Build home control plane inventory and partition plan.
GOAL:
- HOME_INVENTORY.json (ItemList): List every home-relative file in scope (found in context).
- HOME_PARTITIONS.json (ItemList): Group files into logical categories (mcp, router, profiles, etc.).
RULES: JSON only. Follow the ItemList schema strictly. Use deterministic IDs.
```
