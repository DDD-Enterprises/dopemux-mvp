# PROMPT_C14

## Goal
Produce `C14` outputs for phase `C` with strict schema, explicit evidence, and deterministic normalization.
Identify code quality issues, complexity hotspots, and technical debt indicators across all source code: functions exceeding length thresholds, deep nesting, god classes, duplicate logic patterns, missing error handling, and inconsistent coding patterns.

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
- `CODE_HEALTH_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"CODE_HEALTH_SURFACE@v1","items":[...]}`
- Output contracts:
  - `CODE_HEALTH_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `C14`
    - `id_rule`: `CODE_HEALTH_SURFACE:<stable-hash(file_path|function_name|issue_type)>`
    - `required_item_fields`: `id, file_path, function_name, issue_type, severity, description, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "CODE_HEALTH_SURFACE:<hash>",
  "file_path": "<repo-relative path>",
  "function_name": "<function or class name, or null for file-level issues>",
  "issue_type": "high_complexity|long_function|deep_nesting|god_class|duplicate_logic|missing_error_handling|inconsistent_patterns|excessive_parameters|tight_coupling",
  "severity": "critical|high|medium|low",
  "description": "<specific description of the issue>",
  "line_range": [<start>, <end>],
  "metric_value": "<numeric value if applicable, e.g., line count, nesting depth>",
  "metric_threshold": "<threshold that was exceeded>",
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Issue Type Definitions
- **high_complexity**: Cyclomatic complexity indicators (many branches, nested conditions)
- **long_function**: Functions exceeding 100 lines of code
- **deep_nesting**: Nesting depth exceeding 4 levels (if/for/while/try nested inside each other)
- **god_class**: Classes with more than 10 methods or mixing unrelated responsibilities
- **duplicate_logic**: Near-identical code blocks appearing in multiple locations
- **missing_error_handling**: Functions performing I/O, network, or subprocess calls without try/except or error checking
- **inconsistent_patterns**: Same operation done differently in different parts of the codebase (e.g., mixed error handling styles)
- **excessive_parameters**: Functions with more than 5 parameters
- **tight_coupling**: Direct imports crossing architectural boundaries (e.g., service A importing service B internals)

### Severity Classification
- **critical**: Issues that may cause runtime failures or data corruption
- **high**: Issues that significantly impair maintainability or reliability
- **medium**: Issues that moderately affect code quality
- **low**: Style issues or minor improvements

## Extraction Procedure
1. Load upstream CODE_INVENTORY and CODE_PARTITIONS; use the code partition as primary scan surface.
2. Scan for **long functions**: identify functions exceeding 100 lines; record function name, file path, line count.
3. Scan for **deep nesting**: identify code blocks with nesting depth > 4 levels; trace the nesting chain (if > for > if > try > ...).
4. Scan for **god classes**: identify classes with > 10 methods; list method count and method names.
5. Scan for **missing error handling**: identify functions that call `subprocess`, `open()`, `requests.*`, `httpx.*`, database operations, or file I/O without surrounding try/except or explicit error checking.
6. Scan for **excessive parameters**: identify functions with > 5 positional/keyword parameters.
7. Scan for **inconsistent patterns**: compare error handling approaches across modules (e.g., some use exceptions, others return error codes; some log, others swallow).
8. Scan for **duplicate logic**: identify near-identical code blocks (>10 lines) appearing in multiple files.
9. Classify severity for each issue based on impact assessment.
10. Build deterministic IDs using stable content keys `(file_path|function_name|issue_type)`.
11. Attach evidence to every issue with exact excerpts showing the problematic code.
12. Emit exactly `CODE_HEALTH_SURFACE.json` and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
