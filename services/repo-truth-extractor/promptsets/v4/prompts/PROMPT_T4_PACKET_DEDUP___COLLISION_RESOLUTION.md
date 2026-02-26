# PROMPT_T4

## Goal
Produce `T4` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
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
- `TP_BATCHED_PACKETS.partX.md`
- `TP_BATCH_INDEX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_DEDUPED.json`
- `TP_COLLISIONS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_DEDUPED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T4`
    - `id_rule`: `TP_DEDUPED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_COLLISIONS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T4`
    - `id_rule`: `TP_COLLISIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream T-phase packet artifacts (batched packets, batch index, backlog) as specified in the inputs section. Detect duplicate `tp_id` values, duplicate normalized titles, and materially overlapping scopes across all emitted packets.
2. Resolve collisions with deterministic tie-breaks: prefer higher evidence density, then lower blast radius, then earlier dependency position. Preserve traceability from deduped packets to source packet IDs.
3. Record all dropped/merged packets and reason codes in `TP_COLLISIONS.json` with full evidence chains showing which packets were merged and why.
4. Structure the output with clear collision-detection methodology, resolution evidence, and an explicit UNKNOWN section for cases where collision resolution is ambiguous.
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
- Collision resolution tie-break cannot determine winner (identical evidence density and blast radius): retain both packets with `status: unresolved_collision` and flag for manual review.
- Deduplication removes a packet that is a dependency of another: restore the dependency target and re-run collision detection on the affected subgraph.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_T4 — PACKET DEDUP / COLLISION RESOLUTION

TASK: Deduplicate Task Packets and resolve title/id collisions deterministically.

OUTPUTS:
- TP_DEDUPED.json
- TP_COLLISIONS.json

Rules:
- Detect duplicate `tp_id`, duplicate normalized titles, and materially overlapping scopes.
- Resolve collisions with deterministic tie-breaks: higher evidence density, lower blast radius, earlier dependency.
- Preserve traceability from deduped packets to source packet IDs.
- Record dropped/merged packets and reason codes in `TP_COLLISIONS.json`.
```
