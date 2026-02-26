# PROMPT_C11

## Goal
Produce `C11` outputs for phase `C` by extracting deep Leantime integration surfaces across code paths, service boundaries, and event/HTTP interfaces.
This step maps implementation truth, not intended architecture.

## Inputs
- Source scope (scan these roots first):
  - `services/leantime-bridge/**`
  - `src/dopemux/**`
  - `services/**`
  - `config/**`
  - `compose.yml`
  - `docker-compose*.yml`
  - `services/registry.yaml`
- Upstream normalized artifacts:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `EVENT_PRODUCERS.json`
  - `EVENT_CONSUMERS.json`
  - `API_DASHBOARD_SURFACE.json`
  - `SERVICE_CATALOG.partX.json`
  - `SERVICE_CATALOG.json`
  - `REPO_LEANTIME_SURFACE.json`
- Runner context:
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `LEANTIME_INTEGRATION_SURFACE.json`

## Schema
- Deterministic container:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contract:
  - `LEANTIME_INTEGRATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C11`
    - `id_rule`: `LEANTIME_INTEGRATION_SURFACE:<stable-hash(path|symbol|interface)>`
    - `required_item_fields`: `id, path, line_range, evidence`
- Each item should capture one of:
  - service entrypoint integration point
  - HTTP/API boundary call
  - event producer/consumer flow
  - config/env dependency for Leantime behavior

## Extraction Procedure
1. Discover integration candidates from service and core code paths.
2. Validate each candidate using direct evidence (handler, call site, wiring, config key).
3. Build deterministic IDs and normalized item payloads.
4. Attach evidence per field and per relationship.
5. Deduplicate and sort deterministically.
6. Emit exactly one output file.

## Evidence Rules
- Every item and non-derived field requires evidence:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- Evidence must come from repository sources only.
- Use multiple evidence records for cross-file relationships.
- If evidence is incomplete, keep `UNKNOWN` with `missing_evidence_reason`.

## Determinism Rules
- No timestamps or run metadata in norm output.
- Sort items by `(path, line_start, id)` then stable JSON text fallback.
- Deduplicate by `id`.
- Merge evidence as deterministic set union on `(path,line_range,excerpt)`.

## Anti-Fabrication Rules
- Do not invent endpoints, queue topics, events, or dependency links.
- Do not assume any interface is active without explicit evidence.
- Do not synthesize architecture claims unsupported by code/config.
- If uncertain, emit `status: needs_review` rather than guessing.

## Failure Modes
- Missing integration files: emit empty `ItemList` with `coverage_notes`.
- Ambiguous symbol resolution: emit multiple candidates with explicit ambiguity notes.
- Parse failures: preserve partial deterministic output and attach error notes.
- Upstream artifact mismatch: keep extracted evidence and mark unresolved joins.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: C11 - Leantime Integration Surfaces
Phase: C
Step: C11
Outputs:
- LEANTIME_INTEGRATION_SURFACE.json
Mode: extraction
Strict: evidence_only
```
