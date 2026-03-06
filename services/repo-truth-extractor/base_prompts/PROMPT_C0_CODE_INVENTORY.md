# PROMPT C0 — Code Inventory & Partition Plan

## Goal
Scan the **{{ repo.name }}** repository source code and produce a structured inventory of all code modules, packages, and entry points. Partition by language and module boundary for downstream deep extraction.

## Inputs
Scan the following directories and patterns:

{% for scope in scopes.get('C0', ['src/**/*', 'lib/**/*', 'pkg/**/*', 'app/**/*', 'services/**/*', '*.py', '*.ts', '*.js', '*.go', '*.rs', '*.java']) %}
- `{{ scope }}`
{% endfor %}

{% if features.get('http_api_python', {}).get('present') %}
Focus on Python HTTP API code — detected in this project.
{% endif %}
{% if features.get('http_api_node', {}).get('present') %}
Focus on Node.js/TypeScript API code — detected in this project.
{% endif %}

## Outputs
- `CODE_INVENTORY.json`
- `CODE_PARTITIONS.json`

## Schema
```json
{
  "modules": [
    {
      "id": "string (sha256 of path)",
      "path": "string (repo-relative)",
      "language": "string (python|typescript|javascript|go|rust|java|other)",
      "type": "string (module|package|script|config|test|fixture)",
      "line_count": "integer",
      "imports_count": "integer",
      "exports_count": "integer",
      "description": "string (≤100 chars)",
      "evidence": [
        { "path": "string", "line_range": [1, 10], "excerpt": "string ≤200 chars" }
      ]
    }
  ],
  "entry_points": [
    {
      "id": "string",
      "path": "string",
      "type": "string (cli|http|worker|script|main)",
      "evidence": [{ "path": "string", "line_range": [1, 5], "excerpt": "string ≤200 chars" }]
    }
  ],
  "partitions": [
    {
      "partition_id": "string",
      "description": "string",
      "language": "string",
      "file_count": "integer",
      "files": ["string"]
    }
  ]
}
```

## Extraction Procedure
1. Walk the source tree, excluding test fixtures, vendor, node_modules, __pycache__.
2. Identify language for each file by extension.
3. Count lines, detect imports/exports, identify entry points.
4. Categorize each module (module, package, script, test).
5. Group into partitions by language and top-level directory.
6. Emit inventory and partition JSON files.

## Evidence Rules
- Every module must carry ≥1 evidence object with its first meaningful code line.
- `path` must be repo-relative.
- `excerpt` verbatim, ≤200 chars.

## Determinism Rules
- Sort all arrays by `path`.
- Use SHA-256 of path as `id`.
- No timestamps.

## Anti-Fabrication Rules
- Only include files that exist on disk.
- Do not infer module purpose from filename alone.
- If a file has no code (empty), mark as `type: "fixture"`.

## Failure Modes
- If no source files found: emit empty arrays.
- Binary files: skip with note.
- Files over 100K lines: sample first and last 100 lines for evidence.
