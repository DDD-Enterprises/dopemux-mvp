# Validation Output

See `../VALIDATION_OUTPUT.md` for the full validation log.

Key results:

- `pytest -q tests/auditor_router`: `33 passed`
- `scripts/auditor-preflight --help`: passed
- wrapper PAL clink fixture smoke: selected `pal-mcp-clink AVAILABLE`
- wrapper direct fixture smoke: selected `claude-code-cli AVAILABLE`
- pre-commit on changed files: passed

Blocked result:

- GitHub workflow dispatch for PR Steward returned HTTP 500 and is recorded as `BLOCKED_BY_GITHUB_WORKFLOW_DISPATCH_500`.
