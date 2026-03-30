# PROMPT_W4

## Goal
Produce `W4` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`
- `WORKFLOW_CATALOG.json`
- `WORKFLOW_IO_MAP.json`
- `WORKFLOW_COORDINATION_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_FAILURE_RECOVERY.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_FAILURE_RECOVERY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W4`
    - `id_rule`: `WORKFLOW_FAILURE_RECOVERY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**:
    *   Load `WORKFLOW_INVENTORY.json`, `WORKFLOW_PARTITIONS.json`, `WORKFLOW_CATALOG.json`, `WORKFLOW_IO_MAP.json`, `WORKFLOW_COORDINATION_SURFACE.json`.
    *   Define the primary scan surface using the workflow failure modes and recovery partition from `WORKFLOW_PARTITIONS.json`.
    *   Identify all files within the `Source scope` (lines 9-13: `scripts/**`, `services/**`, `docs/02-how-to/**`, `docs/03-reference/**`, `compose.yml`) for detailed content analysis.

2.  **Extract Workflow Failure Modes and Recovery Facts**:
    For each file identified in the scan context, perform the following pattern matching and fact extraction:
    *   **Shell Scripts (`.sh`, `.bash`, etc.)**:
        *   **`set -e`**:
            *   Identify lines containing `set -e` or shell shebangs like `#!/bin/bash -e`.
            *   **Extract**: The presence of `set -e`.
            *   **Classify**: "Script-level exit-on-error".
        *   **`trap`**:
            *   Identify lines containing `trap <command> <signal>`.
            *   **Extract**: The `command` and `signal` arguments (e.g., `trap 'cleanup_func' ERR EXIT`).
            *   **Classify**: "Signal-based recovery/cleanup".
        *   **`rollback` logic**:
            *   Identify functions, blocks, or conditional statements (`if ... then ... else ...`) that contain keywords like `rollback`, `undo`, `cleanup`, `revert`, especially when associated with error conditions or `trap` handlers.
            *   **Extract**: The function/block name, relevant conditional logic, and the commands executed.
            *   **Classify**: "Imperative rollback mechanism".
    *   **Python Files (`.py`)**:
        *   **`try/except`**:
            *   Identify `try: ... except <ExceptionType>: ...` blocks.
            *   **Extract**: The `ExceptionType` (e.g., `IOError`, `Exception` as `e`), the content of the `except` block, and the surrounding function/method.
            *   **Classify**: "Exception handling block".
        *   **`retry` decorators**:
            *   Identify functions/methods decorated with `@retry`, `@tenacity.retry`, or similar patterns (e.g., `from retrying import retry`).
            *   **Extract**: The decorator name, its arguments (e.g., `attempts`, `delay`, `stop_max_attempt_number`), and the decorated function/method name.
            *   **Classify**: "Automated retry mechanism".
        *   **`rollback` logic**:
            *   Identify `finally:` blocks or specific functions/methods (e.g., `_rollback()`, `cleanup_resources()`) that are called within error handling contexts or explicitly named `rollback`, `cleanup`, `undo`.
            *   **Extract**: The function/method name, its arguments, and its execution context (e.g., `finally` block).
            *   **Classify**: "Programmatic rollback mechanism".
    *   **YAML Files (`.yaml`, `compose.yml`, `docs/02-how-to/**.yaml` for CI/CD workflows)**:
        *   **Error handling directives**:
            *   Scan for keys like `restart_policy` (in `compose.yml` services), `on-failure`, `continue-on-error` (in CI/CD job steps), `healthcheck` configurations, `condition: on-failure`.
            *   **Extract**: The service/job/step name, the specific directive (e.g., `restart_policy: on-failure`), and its configured value.
            *   **Classify**: "Declarative failure handling".

3.  **Populate WORKFLOW_FAILURE_RECOVERY Items**:
    *   For each identified fact, construct a `WORKFLOW_FAILURE_RECOVERY` item.
    *   **`id`**: Generate a deterministic ID using `WORKFLOW_FAILURE_RECOVERY:<stable-hash(path|symbol|name|extracted_value)>`. For a `set -e` in a script, `name` could be the script name, and `extracted_value` "set -e".
    *   **`path`**: Record the repo-relative path to the source file (e.g., `scripts/my_script.sh`).
    *   **`line_range`**: Record the exact `[start, end]` line numbers of the evidence.
    *   **`evidence`**: Create an evidence object as per lines 58-63: `{"path": "<repo-relative-path>", "line_range": [<start>, <end>], "excerpt": "<exact substring <=200 chars>"}`. The `excerpt` must be the exact text snippet.
    *   **`type`**: Record the classification from Step 2 (e.g., "Script-level exit-on-error", "Exception handling block").
    *   **`details`**: Include relevant extracted data (e.g., `exception_type`, `retry_attempts`, `trap_signal`, `restart_policy_value`).

4.  **Correlate with Upstream Artifacts**:
    *   For each `WORKFLOW_FAILURE_RECOVERY` item, attempt to link it to specific workflows, services, or I/O operations defined in `WORKFLOW_INVENTORY.json`, `WORKFLOW_CATALOG.json`, `WORKFLOW_IO_MAP.json`, or `WORKFLOW_COORDINATION_SURFACE.json`.
    *   Establish relationships (edges) in the output graph if applicable, documenting the connection with evidence.

5.  **Finalize and Validate Outputs**:
    *   Ensure all `WORKFLOW_FAILURE_RECOVERY` items have an `id`, `path`, `line_range`, and at least one `evidence` object.
    *   Apply deterministic sorting (lines 71-72) and deduplication (lines 73-77) to the `items` list.
    *   Validate all required fields (lines 40-41); emit `UNKNOWN` with `missing_evidence_reason` for unsatisfied values.
    *   Emit exactly one `WORKFLOW_FAILURE_RECOVERY.json` file.
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
# PROMPT_W4 — WORKFLOW FAILURE MODES / RECOVERY

TASK: Identify workflow failure modes and recovery paths.

OUTPUTS:
	•	WORKFLOW_FAILURE_RECOVERY.json
```
