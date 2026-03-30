# PROMPT_W5

## Goal
Produce `W5` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
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
- `WORKFLOW_FAILURE_RECOVERY.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_STATE_COUPLING.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_STATE_COUPLING.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W5`
    - `id_rule`: `WORKFLOW_STATE_COUPLING:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1.  **Initialize Scan Context**:
    *   Load `WORKFLOW_INVENTORY.json`, `WORKFLOW_PARTITIONS.json`, `WORKFLOW_CATALOG.json`, `WORKFLOW_IO_MAP.json`, `WORKFLOW_COORDINATION_SURFACE.json`, `WORKFLOW_FAILURE_RECOVERY.json`.
    *   Define the primary scan surface using the workflow state dependencies (home vs repo) partition from `WORKFLOW_PARTITIONS.json`.
    *   Identify all files within the `Source scope` (lines 9-13: `scripts/**`, `services/**`, `docs/02-how-to/**`, `docs/03-reference/**`, `compose.yml`) for detailed content analysis.

2.  **Extract Workflow State Coupling Facts (Home vs. Repo)**:
    For each file identified in the scan context, perform the following pattern matching and fact extraction to identify paths resolved outside the repository root:
    *   **Python Files (`.py`)**:
        *   **`os.path.expanduser`**:
            *   Identify calls to `os.path.expanduser(<path>)`.
            *   **Extract**: The argument `<path>` and the context of the call.
            *   **Classify**: "Home directory expansion".
        *   **Explicit Home Dir Environment Variables**:
            *   Identify usage of `os.environ.get('HOME')`, `os.getenv('HOME')`, `os.path.expandvars('$HOME')`, `os.path.expandvars('%USERPROFILE%')` or similar in string formatting/concatenation.
            *   **Extract**: The environment variable accessed and its usage context.
            *   **Classify**: "Environment variable based home path".
        *   **Hardcoded Home Paths**:
            *   Identify string literals containing `~`, `/home/`, `/Users/` (e.g., `pathlib.Path('~/config.ini')`, `"/home/user/data"`).
            *   **Extract**: The literal path string.
            *   **Classify**: "Hardcoded absolute/home path".
        *   **Absolute Path Construction/Resolution**:
            *   Identify `os.path.abspath()`, `os.path.realpath()`, or `pathlib.Path.resolve()` calls on paths that are not demonstrably relative to the repository root.
            *   **Extract**: The path argument and the context.
            *   **Classify**: "Absolute path resolution".
    *   **Shell Scripts (`.sh`, `.bash`, etc.)**:
        *   **Tilde `~`**:
            *   Identify usage of `~`, `~/`, `~$USER/`, or similar expansions in commands or assignments.
            *   **Extract**: The specific tilde expansion and its context.
            *   **Classify**: "Shell tilde expansion".
        *   **Explicit Home Dir Environment Variables**:
            *   Identify usage of `$HOME`, `$USERPROFILE`, or similar environment variables in commands or assignments.
            *   **Extract**: The environment variable and its usage context.
            *   **Classify**: "Shell environment variable based home path".
        *   **Hardcoded Home Paths**:
            *   Identify string literals containing `/home/`, `/Users/` (e.g., `cd /home/user/logs`, `cp /Users/shared/file`).
            *   **Extract**: The literal path string.
            *   **Classify**: "Hardcoded absolute/home path".
        *   **Absolute Path Resolution Commands**:
            *   Identify commands like `readlink -f`, `realpath` when applied to paths that may resolve outside the repository.
            *   **Extract**: The command and its path argument.
            *   **Classify**: "Shell absolute path resolution".
    *   **YAML Files (`.yaml`, `compose.yml`, `docs/02-how-to/**.yaml` for configuration)**:
        *   **Hardcoded Home Paths**:
            *   Identify string values for volume mounts, paths, or configuration parameters containing `~`, `/home/`, `/Users/` (e.g., `volumes: - ~/data:/app/data`, `config_path: /Users/shared/config.json`).
            *   **Extract**: The path string and its YAML key context.
            *   **Classify**: "Declarative hardcoded absolute/home path".
        *   **Environment Variable Usage**:
            *   Identify use of environment variable syntax like `${HOME}` or `$HOME` within path strings.
            *   **Extract**: The environment variable used in the path.
            *   **Classify**: "Declarative environment variable path".
    *   **Identify codebase reaching outside repository root**: For each identified path, determine if it resolves to a location *not* contained within the repository's root directory. This is the primary criterion for an item of type `WORKFLOW_STATE_COUPLING`.

3.  **Populate WORKFLOW_STATE_COUPLING Items**:
    *   For each identified fact representing a state dependency outside the repository root, construct a `WORKFLOW_STATE_COUPLING` item.
    *   **`id`**: Generate a deterministic ID using `WORKFLOW_STATE_COUPLING:<stable-hash(path|symbol|name|extracted_path_expression)>`. For a `~/config`, `name` could be the variable name or file, and `extracted_path_expression` "`/~/config`".
    *   **`path`**: Record the repo-relative path to the source file (e.g., `services/my_service/main.py`).
    *   **`line_range`**: Record the exact `[start, end]` line numbers of the evidence.
    *   **`evidence`**: Create an evidence object as per lines 58-63: `{"path": "<repo-relative-path>", "line_range": [<start>, <end>], "excerpt": "<exact substring <=200 chars>"}`. The `excerpt` must be the exact text snippet.
    *   **`type`**: Record the classification from Step 2 (e.g., "Home directory expansion", "Hardcoded absolute/home path").
    *   **`expression`**: Store the extracted path expression (e.g., `os.path.expanduser('~/.config')`, `~/data`, `/home/user/logs`, `$HOME/cache`).
    *   **`is_absolute`**: Boolean indicating if the path expression is inherently absolute or resolves to an absolute path.
    *   **`is_home_relative`**: Boolean indicating if the path expression uses `~` or `$HOME`.

4.  **Correlate with Upstream Artifacts**:
    *   For each `WORKFLOW_STATE_COUPLING` item, attempt to link it to specific workflows or services defined in `WORKFLOW_INVENTORY.json` or `WORKFLOW_CATALOG.json`.
    *   Establish relationships (edges) in the output graph if applicable, documenting the connection with evidence.

5.  **Finalize and Validate Outputs**:
    *   Ensure all `WORKFLOW_STATE_COUPLING` items have an `id`, `path`, `line_range`, and at least one `evidence` object.
    *   Apply deterministic sorting (lines 71-72) and deduplication (lines 73-77) to the `items` list.
    *   Validate all required fields (lines 40-41); emit `UNKNOWN` with `missing_evidence_reason` for unsatisfied values.
    *   Emit exactly one `WORKFLOW_STATE_COUPLING.json` file.
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
- Hidden dependency: if an element depends on something not explicitly documented, emit with `status: implicit_dependency`
- Shadowed config: if a config overrides another at a different level, emit both with `status: shadow`

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_W5 — WORKFLOW STATE DEPENDENCIES / HOME VS REPO

TASK: Extract workflow state coupling points.

OUTPUTS:
	•	WORKFLOW_STATE_COUPLING.json
```
