# PROMPT_D3

## Goal
Produce `D3` outputs for phase `D` with strict schema, explicit evidence, and deterministic normalization.
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
- `DOC_INTERFACES.partX.json`
- `DOC_WORKFLOWS.partX.json`
- `DOC_DECISIONS.partX.json`
- `DOC_GLOSSARY.partX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOC_CITATION_GRAPH.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOC_CITATION_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `D3`
    - `id_rule`: `DOC_CITATION_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream `DOC_INVENTORY.json`, `DOC_PARTITIONS.json`, and D1/D2 artifacts; use the full doc inventory as the scan surface for citation discovery.
2. Build citation graph edges: for each document, identify references to other documents via markdown links, filename mentions, "see also" annotations, explicit citations, and section anchors; record source document, target document, citation type, and file:line evidence.
3. Build doc-to-code edges: identify references from documents to code paths (file paths, function names, class references, module imports mentioned in prose); record the doc source, code target, and reference type.
4. Detect bidirectional references: identify cases where doc A references doc B and doc B references doc A; record as bidirectional edges.
5. For each DOC_CITATION_GRAPH item, populate `id`, graph nodes, graph edges, and `evidence`.
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
- Broken link: if a citation references a document or code path that does not exist, emit the edge with `status: broken_link` and `missing_evidence_reason`.
- Ambiguous code reference: if a document mentions a code element that matches multiple files or symbols, emit edges to all candidates with `status: ambiguous` and evidence of each match.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: DOC_CITATION_GRAPH.json

Prompt:
- Build graph edges:
  - doc A references doc B (links, filenames, "see also", explicit citations)
  - doc A references code path
  - doc A references service name/config name
- Output top referenced docs, hub docs, cross-plane edges.
```
