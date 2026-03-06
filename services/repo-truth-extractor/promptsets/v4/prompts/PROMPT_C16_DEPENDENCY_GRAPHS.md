# PROMPT_C16

## Goal
Produce `C16` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Build module-level and service-level dependency graphs using edges-as-items representation. Map import chains, service-to-service calls, and cross-boundary dependencies.

## Inputs
- Source scope (scan these roots first):
  - `src/**/*.py`
  - `services/**/*.py`
  - `components/**/*.py`
  - `compose.yml`
  - `docker-compose*.yml`
  - `services/registry.yaml`
  - `pyproject.toml`
  - `requirements*.txt`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_CATALOG.json`
  - `SERVICE_ENTRYPOINTS.json`
  - `EVENTBUS_SURFACE.json`
  - `EVENT_PRODUCERS.json`
  - `EVENT_CONSUMERS.json`
  - `PYTHON_API_SURFACE.json`
  - `SERVICE_ENDPOINT_SURFACE.json`
  - `AGENT_ORCHESTRATION_SURFACE.json`
  - `WORKFLOW_RUNNER_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `MODULE_DEPENDENCY_GRAPH.json`
- `SERVICE_DEPENDENCY_GRAPH.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts (edges-as-items — no `json_graph` kind in runner):
  - `MODULE_DEPENDENCY_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C16`
    - `id_rule`: `MODULE_DEP_EDGE:<stable-hash(source|target|edge_type)>`
    - `required_item_fields`: `id, source, target, edge_type, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
  - `SERVICE_DEPENDENCY_GRAPH.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C16`
    - `id_rule`: `SERVICE_DEP_EDGE:<stable-hash(source|target|edge_type)>`
    - `required_item_fields`: `id, source, target, edge_type, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `edge_type` enum for module graph: `import | from_import | dynamic_import | type_reference | inheritance | composition`
- `edge_type` enum for service graph: `http_call | mcp_invocation | eventbus_pub_sub | shared_db | file_dependency | compose_depends_on | direct_import`
- Each item represents ONE directed edge: `source` → `target` with `edge_type`
- `source` and `target` are module paths (for MODULE) or service_ids (for SERVICE)

## Extraction Procedure
1. Load upstream inventory and partitions; use the full code partition as scan surface
2. **Module dependency graph**: scan all Python files for `import` and `from ... import` statements
3. Classify each import: `import` (full module), `from_import` (selective), `dynamic_import` (`importlib` calls)
4. Trace inheritance chains: extract class bases to build `inheritance` edges
5. Identify composition patterns: class attributes typed as other project classes → `composition` edges
6. **Service dependency graph**: cross-reference upstream artifacts to build service-level edges
7. From `EVENTBUS_SURFACE.json`: map producer service → consumer service as `eventbus_pub_sub` edges
8. From `SERVICE_ENDPOINT_SURFACE.json`: identify cross-service HTTP calls and MCP invocations
9. From `compose.yml` / `docker-compose*.yml`: extract `depends_on` relationships as `compose_depends_on` edges
10. From `SERVICE_CATALOG.json`: extract declared dependencies
11. Build deterministic IDs: `MODULE_DEP_EDGE:<hash(source|target|edge_type)>` and `SERVICE_DEP_EDGE:<hash(source|target|edge_type)>`
12. Attach evidence to every edge (the import statement, the compose config line, the API call site)
13. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash)
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps
15. Emit exactly the declared outputs and no additional files

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
- Every edge MUST cite the source code location where the dependency is established.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(source, target, edge_type, id)` to ensure stable edge ordering.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent dependencies, import chains, or service relationships.
- Do not infer service dependencies from naming conventions alone; require direct code/config evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.
- Do not assume a service depends on another because they share a database without explicit evidence.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Circular dependencies: emit all cycle edges normally; downstream synthesis (S9) handles cycle detection.
- Conditional imports: if an import is inside `if TYPE_CHECKING:` or try/except, emit with `status: conditional`.
- External dependencies: only include edges to project-internal modules/services; skip stdlib and third-party.
