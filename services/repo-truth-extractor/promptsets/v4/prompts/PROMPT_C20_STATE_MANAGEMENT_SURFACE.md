# PROMPT_C20

## Goal
Produce `C20` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract mutable state-management surfaces across the codebase: instance attribute mutation, module globals, cache mutation, SQLite and Redis writes, and other stateful update paths that affect runtime behavior or durability.

## Inputs
- Source scope (scan these roots first):
  - `src/**`
  - `services/**`
  - `shared/**`
  - `plugins/**`
  - `config/**`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `DOPE_MEMORY_DB_WRITES.json`
  - `WORKFLOW_RUNNER_SURFACE.json`
  - `SERVICE_CATALOG.partX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `STATE_MANAGEMENT_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"STATE_MANAGEMENT_SURFACE@v1","items":[...]}`
- Output contracts:
  - `STATE_MANAGEMENT_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C20`
    - `id_rule`: `STATE_MANAGEMENT_SURFACE:<stable-hash(path|symbol|state_type|mutation_kind)>`
    - `required_item_fields`: `id, state_type, mutation_kind, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `state_type` enum:
  - `instance_attribute`
  - `module_global`
  - `sqlite_write`
  - `redis_write`
  - `cache_mutation`
  - `session_state`
- `mutation_kind` enum:
  - `assignment`
  - `append_or_extend`
  - `setdefault_or_update`
  - `delete`
  - `persistence_write`

## Extraction Procedure
1. Load upstream code partitions, DB-write artifacts, workflow surfaces, and service catalog context.
2. Scan for `self.` or class-owned mutable assignments inside methods that persist state beyond local scope.
3. Scan for module-level globals and mutable registries that are reassigned, appended to, or cleared at runtime.
4. Scan for SQLite writes such as `INSERT`, `UPDATE`, `DELETE`, ORM `commit()`, and file-backed state writes; cross-reference `DOPE_MEMORY_DB_WRITES.json` where relevant.
5. Scan for Redis or cache writes such as `set`, `hset`, `incr`, `expire`, or custom cache wrappers.
6. Scan for session mutation patterns in web handlers or middleware where state is persisted between requests.
7. Build deterministic IDs from `(path|symbol|state_type|mutation_kind)` and record concrete evidence of the mutation site.
8. Normalize arrays by stable sort keys, deduplicate by ID, and emit exactly `STATE_MANAGEMENT_SURFACE.json`.

## Evidence Rules
- Every item must include exact source excerpts showing the mutation call or assignment.
- Every evidence object must include `path`, `line_range`, and `excerpt`.
- If a helper abstracts persistence, include evidence from both the helper invocation and the helper body when both are required to prove the write.
- Use repo-relative paths only.
- If the storage backend is uncertain, keep `state_type` as `UNKNOWN` rather than guessing between cache or durable store.

## Determinism Rules
- Do not emit run-local state snapshots, counts, or timestamps.
- Sort `items` by `(path, line_start, id)`.
- Use enum values exactly as declared and avoid near-duplicate categories.
- Merge duplicate items by deterministic ID and evidence union only.

## Anti-Fabrication Rules
- Do not classify local temporary variables as state-management surfaces.
- Do not infer Redis or SQLite usage from dependency declarations alone; require code or SQL evidence.
- Do not claim durability for in-memory caches unless a persistence write is separately evidenced.
- Do not merge read-only access sites into mutation records.

## Failure Modes
- If a mutation occurs through reflection, metaprogramming, or generated code, keep the directly visible mutation site only.
- If a function both reads and writes shared state, emit the write surface and ignore read-only lines unless needed for context.
- If multiple mutation kinds occur in one block, emit separate items when they materially differ.
- If the symbol name is unavailable, preserve the nearest enclosing function or class name and mark the missing detail explicitly.
