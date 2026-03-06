# PROMPT A0 — Repo Control Inventory & Partition Plan

## Goal
Scan the **{{ repo.name }}** repository control plane and produce a complete inventory of all control-plane files (compose manifests, Makefiles, CI configs, package manifests, scripts, and configuration files).

## Inputs
Scan the following directories and file patterns within the repository:

{% for scope in scopes.get('A0', ['compose*.yml', 'docker-compose*.yml', 'Makefile', 'Taskfile.yml', 'pyproject.toml', 'package.json', 'Cargo.toml', '.github/workflows/*.yml', 'scripts/**/*.sh', 'config/**/*']) %}
- `{{ scope }}`
{% endfor %}

Include hidden directories: `.github/`, `.pre-commit-config.yaml`, `.gitlab-ci.yml`.
Examine all top-level configuration files.
{% if features.get('docker_compose', {}).get('present') %}
Pay special attention to Docker Compose files — this project uses Docker Compose.
{% endif %}
{% if features.get('ci_github_actions', {}).get('present') %}
Include all GitHub Actions workflows in `.github/workflows/`.
{% endif %}

## Outputs
- `REPOCTRL_INVENTORY.json`
- `REPOCTRL_PARTITIONS.json`

## Schema
```json
{
  "control_files": [
    {
      "id": "string (sha256 of repo-relative path)",
      "path": "string (repo-relative)",
      "category": "string (compose|makefile|ci|package|config|script|iac)",
      "description": "string (≤100 chars)",
      "line_count": "integer",
      "evidence": [
        { "path": "string", "line_range": [1, 10], "excerpt": "string ≤200 chars" }
      ]
    }
  ],
  "partitions": [
    {
      "partition_id": "string",
      "description": "string",
      "file_count": "integer",
      "files": ["string (repo-relative path)"]
    }
  ],
  "summary": {
    "total_files": "integer",
    "by_category": { "compose": 0, "makefile": 0, "ci": 0 }
  }
}
```

## Extraction Procedure
1. Walk the repo tree top-down, applying include/exclude globs.
2. Match each file against known control-plane patterns (compose, makefile, CI, package, config, script, IaC).
3. Categorize each match; read first 50 lines for evidence.
4. Group into logical partitions by function (build, deploy, test, config).
5. Compute summary counts.
6. Emit `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`.

## Evidence Rules
- Every item must carry ≥1 evidence object.
- `path` must be repo-relative (no absolute paths).
- `excerpt` must be verbatim, ≤200 chars. No paraphrasing.
- `line_range` must be [start, end] inclusive, 1-indexed.

## Determinism Rules
- Sort all arrays by `id` or `path`.
- Use SHA-256 of repo-relative path as `id`.
- No timestamps, random values, or non-deterministic data in output.

## Anti-Fabrication Rules
- If a file does not exist on disk, do not include it.
- If content is ambiguous, mark `category` as `"unknown"`.
- Never infer file purpose from name alone — read content.

## Failure Modes
- If repo has zero control files: emit valid JSON with empty arrays.
- If a file cannot be read (permissions): skip with note in `description`.
- If file count exceeds 500: partition and process in batches.
