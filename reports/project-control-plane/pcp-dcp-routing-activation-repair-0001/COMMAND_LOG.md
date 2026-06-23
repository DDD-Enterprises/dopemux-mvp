# Command Log

| cwd | command | exit | artifact |
|---|---|---:|---|
| worktree | `python -m pytest -q tests/project_control_plane tests/dcp_extension` | 0 | TEST_RESULTS.md |
| worktree | `python -m compileall -q src/dopemux/pcp tests/project_control_plane tests/dcp_extension` | 0 | — |
| worktree | Draft202012Validator schema check (8 schemas) | 0 | SCHEMA_VALIDATION_REPORT.json |
| worktree | `git diff --check` | 0 | — |
| worktree | `python -m build --wheel` (via packaging test) | 0 | test_packaging_pcp.py |