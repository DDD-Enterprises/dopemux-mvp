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

## Hard Output Contract
- Output JSON only. No prose, markdown fences, commentary, or multiple JSON objects.
- Treat the runner context as line-numbered evidence. Every cited `line_range` MUST use the line numbers shown in the provided excerpt.
- Every `items[]` entry MUST include `id`, `path`, and `line_range`.
- Every evidence object MUST include repo-relative `path`, integer `line_range`, and exact `excerpt`.
- If a value cannot be grounded from the provided excerpt, return valid JSON with `UNKNOWN` or fail-closed placeholders; never invent line numbers.

## Hard Requirements
- Every `payload.items[]` row MUST include:
  - `id` as a string
  - `path` as a repo-relative string
  - `line_range` as `[start, end]` with exactly two integers where `start > 0` and `end >= start`
- For every emitted row, `evidence[0].path` and `evidence[0].line_range` MUST match the row's `path` and `line_range`.
- Treat the provided excerpts as line-numbered evidence. Cite only those excerpt-local line numbers.
- If you cannot determine a real `line_range` from the provided evidence, do not guess.
- Instead, emit a valid artifact envelope with `"items": []` for that artifact.
- Output exactly one JSON object. No markdown, no prose, no code fences.

## Minimal Example
```json
{
  "artifacts": [
    {
      "artifact_name": "DOC_INDEX.partX.json",
      "payload": {
        "schema": "DOC_INDEX@v1",
        "items": [
          {
            "id": "DOC_INDEX:example",
            "path": "docs/example.md",
            "line_range": [7, 9],
            "name": "Example doc",
            "kind": "contract",
            "evidence": [
              {
                "path": "docs/example.md",
                "line_range": [7, 9],
                "excerpt": "0007: Example contract statement"
              }
            ]
          }
        ]
      }
    }
  ]
}
```

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
1. Load upstream inventory and partitions; use the doc claims, boundaries, and supersession partition as primary scan surface
2. Extract doc claims, boundaries, and supersession facts: scan relevant files for domain-specific patterns and structures
3. Build relationship graph: trace connections between extracted doc claims, boundaries, and supersession elements
4. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts
5. For each DOC_INDEX item, populate `id`, required fields, and `evidence`
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

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
