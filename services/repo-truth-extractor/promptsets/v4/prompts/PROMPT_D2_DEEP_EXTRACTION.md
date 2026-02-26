# PROMPT_D2

## Goal
Produce `D2` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
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
- `DOC_INDEX.partX.json`
- `DOC_CONTRACT_CLAIMS.partX.json`
- `DOC_BOUNDARIES.partX.json`
- `DOC_SUPERSESSION.partX.json`
- `CAP_NOTICES.partX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_INTERFACES.partX.json`
- `DOC_WORKFLOWS.partX.json`
- `DOC_DECISIONS.partX.json`
- `DOC_GLOSSARY.partX.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_INTERFACES.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_INTERFACES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_WORKFLOWS.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_WORKFLOWS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_DECISIONS.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_DECISIONS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOC_GLOSSARY.partX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D2`
    - `id_rule`: `DOC_GLOSSARY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. For each document flagged in D1 CAP_NOTICES or requiring deep extraction, parse structured interface definitions: service responsibility matrices, API endpoint tables, data flow diagrams described in text, and schema references. Record each interface with its declaring document and line range evidence.
2. Extract workflow descriptions: multi-step procedures, operational runbooks, pipeline definitions, and state machine descriptions found in documentation. For each workflow, record the steps, the services involved, event names mentioned, and any referenced state databases or schemas.
3. Locate decision records: sections titled `Decision`, `ADR`, `RFC`, or containing decision rationale language (`we chose X because`, `alternative considered`). Extract the decision summary, rationale, alternatives considered, and status (accepted/rejected/superseded).
4. Build a glossary from explicitly defined terms: definitions following patterns like `**term**: definition`, `term - definition`, or glossary sections. Record each term, its definition, the defining document, and line range evidence.
5. Cross-reference extracted interfaces and workflows against upstream C-phase artifacts (`SERVICE_ENTRYPOINTS.json`, `EVENTBUS_SURFACE.json`) to validate that documented interfaces match code reality. Flag discrepancies with `status: doc_code_mismatch`.
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
- Workflow description references services or events not found in any upstream artifact: emit with referenced names and `status: unresolved_reference` with evidence from the document.
- Decision record has no explicit status (accepted/rejected): emit with `status: UNKNOWN` and `missing_evidence_reason: no_decision_status`.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal (per partition):
- DOC_INTERFACES.partX.json
- DOC_WORKFLOWS.partX.json
- DOC_DECISIONS.partX.json
- DOC_GLOSSARY.partX.json

Prompt:
- Extract structured interface/workflow details:
  - service responsibilities
  - dataflow steps
  - event names mentioned
  - state DBs and schema references
  - operational workflows, multi-service pipelines
  - instruction-file-driven workflows
- Again: cite everything.
```
