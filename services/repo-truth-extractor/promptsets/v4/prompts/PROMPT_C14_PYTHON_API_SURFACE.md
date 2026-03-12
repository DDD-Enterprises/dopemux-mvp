# PROMPT_C14

## Goal
Produce `C14` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Extract the Python API surface: public modules, `__all__` exports, typed entrypoints, importable symbols, and package structure to map the programmatic API of the codebase.

## Inputs
- Source scope (scan these roots first):
  - `src/**/*.py`
  - `src/dopemux/**`
  - `services/**/*.py`
  - `components/**/*.py`
  - `setup.py`
  - `setup.cfg`
  - `pyproject.toml`
- Upstream normalized artifacts available to this step:
  - `CODE_INVENTORY.json`
  - `CODE_PARTITIONS.json`
  - `SERVICE_ENTRYPOINTS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PYTHON_API_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `PYTHON_API_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C14`
    - `id_rule`: `PYTHON_API_SURFACE:<stable-hash(path|module|symbol)>`
    - `required_item_fields`: `id, module_path, symbol_name, symbol_type, visibility, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `symbol_type` enum: `function | class | constant | type_alias | module | package | variable`
- `visibility` enum: `public_all | public_no_underscore | protected | private`
- For `function` and `class` items, include: `signature`, `parameters`, `return_type`, `docstring_summary`
- For `module` items, include: `all_exports` (list of names in `__all__`), `implicit_exports` (public names without `__all__`)

## Extraction Procedure
1. Load upstream inventory and partitions; use the Python source partition as primary scan surface
2. Scan all `__init__.py` files to build the package tree and identify re-exports
3. For each module, check for `__all__` definition — extract the explicit export list with evidence
4. For modules without `__all__`, identify public symbols (no leading underscore) as implicit exports
5. Extract typed entrypoints: functions and classes with type annotations on parameters and return values
6. Scan `pyproject.toml` / `setup.py` / `setup.cfg` for `[project.scripts]`, `console_scripts`, and package metadata
7. For each public symbol, extract: name, type (function/class/constant), signature, docstring summary
8. Cross-reference with `SERVICE_ENTRYPOINTS.json` to identify which API symbols serve as service entry points
9. Build deterministic IDs using stable content keys (path/module/symbol)
10. Attach evidence to every non-derived field and every relationship edge
11. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash)
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps
13. Emit exactly the declared outputs and no additional files

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
- Do not invent API symbols, type annotations, or module structures.
- Do not infer function signatures from usage sites; require direct definition evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.
- Do not assume a function is public because it lacks an underscore; check `__all__` first.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Dynamic exports: if `__all__` is computed at runtime, emit with `status: dynamic_all` and capture the computation evidence.
- Star imports: if a module uses `from x import *`, emit with `status: star_import` and trace the imported symbols.
