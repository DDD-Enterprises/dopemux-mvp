# PROMPT G0 — Governance & Quality Inventory

## Goal
Scan the **{{ repo.name }}** repository for governance artifacts: CI/CD pipelines, quality gates, pre-commit hooks, linting configs, test configurations, and code review policies.

## Inputs
Scan the following:

{% for scope in scopes.get('G0', ['.github/**/*', '.pre-commit-config.yaml', '.eslintrc*', '.flake8', 'tox.ini', 'pytest.ini', 'pyproject.toml', '.editorconfig', 'CODEOWNERS', '.gitignore']) %}
- `{{ scope }}`
{% endfor %}

{% if features.get('ci_github_actions', {}).get('present') %}
Analyze GitHub Actions workflows for quality gates and enforcement.
{% endif %}

## Outputs
- `GOVERNANCE_INVENTORY.json`

## Schema
```json
{
  "ci_pipelines": [
    {
      "id": "string",
      "path": "string",
      "platform": "string (github_actions|gitlab_ci|jenkins|circleci|other)",
      "triggers": ["string"],
      "jobs": ["string"],
      "evidence": [{ "path": "string", "line_range": [1, 5], "excerpt": "string ≤200 chars" }]
    }
  ],
  "quality_tools": [
    {
      "id": "string",
      "tool": "string (eslint|flake8|mypy|prettier|black|isort|other)",
      "config_path": "string",
      "enforced_in_ci": "boolean"
    }
  ],
  "pre_commit_hooks": [
    {
      "id": "string",
      "hook_id": "string",
      "repo": "string",
      "stages": ["string"]
    }
  ],
  "policies": [
    {
      "id": "string",
      "path": "string",
      "type": "string (codeowners|contributing|security|license)",
      "evidence": [{ "path": "string", "line_range": [1, 5], "excerpt": "string ≤200 chars" }]
    }
  ]
}
```

## Extraction Procedure
1. Scan `.github/workflows/` for CI pipeline definitions.
2. Detect quality tool configs (eslint, flake8, mypy, black, prettier).
3. Parse `.pre-commit-config.yaml` for hooks.
4. Find policy files (CODEOWNERS, CONTRIBUTING, SECURITY).
5. Cross-reference: is each quality tool enforced in CI?
6. Emit governance inventory.

## Evidence Rules
- Every item must cite its config file with line range.
- `path` repo-relative.
- `excerpt` verbatim, ≤200 chars.

## Determinism Rules
- Sort by `id`.
- No timestamps.

## Anti-Fabrication Rules
- Only report tools with config files present.
- Do not infer CI enforcement without evidence.

## Failure Modes
- No CI found: emit empty `ci_pipelines` array.
- Malformed YAML: report error, continue with other files.
