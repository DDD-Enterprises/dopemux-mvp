# PROMPT_T3

## Goal
Produce `T3` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`
- `TP_PACKETS_TOP10.partX.md`
- `TP_PACKET_IMPLEMENTATION_INDEX.json`
- `TP_SCHEMA.json`
- `TP_AUTHORITY_RULES.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_BATCHED_PACKETS.partX.md`
- `TP_BATCH_INDEX.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_BATCHED_PACKETS.partX.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `T3`
    - `id_rule`: `TP_BATCHED_PACKETS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `TP_BATCH_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T3`
    - `id_rule`: `TP_BATCH_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
2. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
3. Attach evidence to every non-derived field and every relationship edge.
4. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
5. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
6. Emit exactly the declared outputs and no additional files.

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

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_T3 — PACKET GENERATION / BATCHED

TASK: Generate implementation-ready Task Packets in deterministic batches from R and X norm artifacts.

OUTPUTS:
- TP_BATCHED_PACKETS.partX.md
- TP_BATCH_INDEX.json

Rules:
- Emit packets in stable order by priority, then `tp_id`.
- Each packet must include: objective, scope in/out, invariants, plan, exact commands, acceptance criteria, rollback, stop conditions.
- Each packet must include a commit plan and explicit acceptance gates.
- Every load-bearing claim must cite `authority_inputs` paths.
- If output exceeds context, split into `.partX` artifacts and include full index references in `TP_BATCH_INDEX.json`.
```
