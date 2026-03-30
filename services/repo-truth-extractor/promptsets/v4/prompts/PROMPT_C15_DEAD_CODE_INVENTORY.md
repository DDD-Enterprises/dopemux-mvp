# PROMPT_C15

## Goal
Produce `C15` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Identify unreachable, unused, and deprecated code: functions/classes never imported or called from other modules, stub implementations, deprecated markers, commented-out code blocks, and unused imports.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `shared/**`
- `plugins/**`
- `tools/**`
- `scripts/**`
- Upstream normalized artifacts available to this step:
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`
- `SERVICE_ENTRYPOINTS.json`
- `SERVICE_CATALOG.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DEAD_CODE_INVENTORY.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"DEAD_CODE_INVENTORY@v1","items":[...]}`
- Output contracts:
  - `DEAD_CODE_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C15`
    - `id_rule`: `DEAD_CODE_INVENTORY:<stable-hash(file_path|symbol_name|dead_code_type)>`
    - `required_item_fields`: `id, file_path, symbol_name, symbol_type, dead_code_type, confidence, evidence, referenced_by`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "DEAD_CODE_INVENTORY:<hash>",
  "file_path": "<repo-relative path>",
  "symbol_name": "<function, class, variable, or import name>",
  "symbol_type": "function|class|method|variable|import|module",
  "dead_code_type": "unreferenced|unreachable|deprecated_marker|empty_implementation|commented_out|stub_only|unused_import",
  "confidence": "high|medium|low",
  "line_range": [<start>, <end>],
  "referenced_by": ["<list of files/modules that reference this symbol, empty if truly dead>"],
  "deprecation_marker": "<text of @deprecated decorator or comment, if applicable>",
  "description": "<why this is considered dead code>",
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Dead Code Type Definitions
- **unreferenced**: Functions/classes defined but never imported or called from any other module in the scanned scope.
- **unreachable**: Code after unconditional return/raise/break/continue, or inside branches that can never execute (e.g., `if False:`).
- **deprecated_marker**: Symbols marked with `@deprecated`, `# DEPRECATED`, `DeprecationWarning`, or similar markers.
- **empty_implementation**: Functions/methods whose body is only `pass`, `...`, or `raise NotImplementedError`.
- **commented_out**: Code blocks that are commented out (multi-line `#` blocks or triple-quote disabled code).
- **stub_only**: Functions that exist only as stubs with `# TODO` or placeholder logic.
- **unused_import**: Import statements where the imported name is never used in the module.

### Confidence Levels
- **high**: Symbol is demonstrably unreferenced across all scanned files, or has explicit deprecation marker.
- **medium**: Symbol appears unreferenced but could be used via dynamic dispatch, reflection, or entry points not in scan scope.
- **low**: Symbol might be dead but evidence is ambiguous (e.g., used only in tests, or referenced via string-based lookup).

## Extraction Procedure
1. Load upstream CODE_INVENTORY and CODE_PARTITIONS; use the code partition as primary scan surface.
2. Scan for **unreferenced symbols**: for each public function/class definition, search for import statements and call sites across all modules in scope. If no references found outside the defining module, flag as unreferenced.
3. Scan for **unreachable code**: identify code after unconditional `return`, `raise`, `sys.exit()`, `break`, `continue`; also identify `if False:` or `if 0:` blocks.
4. Scan for **deprecated markers**: search for `@deprecated`, `# DEPRECATED`, `warnings.warn(.*DeprecationWarning)`, `# TODO: remove`, `# LEGACY`.
5. Scan for **empty implementations**: find functions/methods whose body is exactly `pass`, `...`, `raise NotImplementedError()`, or `raise NotImplementedError`.
6. Scan for **commented-out code**: identify blocks of 5+ consecutive commented lines that appear to be code (contain `=`, `def `, `class `, `import `, `if `, `for `, `return `).
7. Scan for **stub implementations**: find functions with `# TODO` in body or with placeholder return values and no real logic.
8. Scan for **unused imports**: for each import statement, check if the imported name appears anywhere else in the module.
9. For unreferenced symbols, populate `referenced_by` with any partial references found (e.g., test files, dynamic usage).
10. Assign confidence based on reference analysis completeness and dynamic dispatch possibility.
11. Build deterministic IDs using stable content keys `(file_path|symbol_name|dead_code_type)`.
12. Emit exactly `DEAD_CODE_INVENTORY.json` and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
