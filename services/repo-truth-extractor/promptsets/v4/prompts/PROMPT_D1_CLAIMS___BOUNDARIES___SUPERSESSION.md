# PROMPT_D1

## Goal
Produce `D1` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `docs/**`
- `README.md`
- `CHANGELOG.md`
- `docs/docs_index.yaml`
- Upstream normalized artifacts available to this step:
- `DOC_INVENTORY.json`
- `DOC_PARTITIONS.json`
- `DOC_TODO_QUEUE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_INDEX.partX.json`
- `DOC_CONTRACT_CLAIMS.partX.json`
- `DOC_BOUNDARIES.partX.json`
- `DOC_SUPERSESSION.partX.json`
- `CAP_NOTICES.partX.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_INDEX.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D1`
    - `id_rule`: `DOC_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
  - `DOC_CONTRACT_CLAIMS.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D1`
    - `id_rule`: `DOC_CONTRACT_CLAIMS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_BOUNDARIES.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D1`
    - `id_rule`: `DOC_BOUNDARIES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_SUPERSESSION.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D1`
    - `id_rule`: `DOC_SUPERSESSION:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `CAP_NOTICES.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D1`
    - `id_rule`: `CAP_NOTICES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Scan each document in the assigned partition for normative statements: keywords `MUST`, `SHALL`, `DO NOT`, `REQUIRED`, `INVARIANT`, and authority language (`this document governs`, `the canonical source is`). For each normative claim, record the exact statement, its scope, and file path with line range evidence.
2. Extract boundary declarations: statements defining plane boundaries (PM plane, cognitive plane, memory plane), interface contracts between planes, and enforcement mechanisms (even if planned/aspirational). Record each boundary with the declaring document and line range.
3. Identify supersession markers: `ACTIVE`, `DEPRECATED`, `SUPERSEDED BY`, version headers (e.g., `v2.0`), timestamps in document metadata, and explicit `supersedes: <doc>` declarations. Build a supersession chain linking newer documents to the ones they replace.
4. Extract contract claims: explicit interface specifications, API contracts, schema definitions, and SLA declarations found in documentation. Record the contract type, parties involved, and evidence.
5. Generate `CAP_NOTICES` for content that exceeds extraction capacity or needs deeper analysis in D2: documents with >5000 tokens, documents with embedded code blocks requiring interpretation, and documents referencing external specs not in the repository.
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
- Document contains conflicting normative statements (e.g., `MUST use X` in one section and `MUST NOT use X` in another): emit both claims with distinct IDs and `status: conflicting_claims` with evidence from each location.
- Supersession target document referenced but not found in repository: emit supersession edge with `target_status: not_found` and evidence citing the reference.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal (per partition):
- DOC_INDEX.partX.json
- DOC_CONTRACT_CLAIMS.partX.json
- DOC_BOUNDARIES.partX.json
- DOC_SUPERSESSION.partX.json
- CAP_NOTICES.partX.json (what didn't fit, what needs D2)

Prompt:
- Extract only "normative" and "boundary" statements:
  - MUST/SHALL/DO NOT, invariants, failure modes, interfaces, "authority" language
  - plane boundaries and what enforces them (even if just planned)
  - supersession markers: ACTIVE/DEPRECATED, version headers, timestamps, "supersedes"
- Cite everything: file + line_range + short quote.
```
