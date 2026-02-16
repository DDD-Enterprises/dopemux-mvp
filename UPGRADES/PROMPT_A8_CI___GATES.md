Goal: REPO_CI_GATES.json

Prompt:
- Extract gates from:
  - .github/workflows/**, .pre-commit-config.yaml, ruff/mypy/pytest configs, Makefile.
- Output:
  - gate name -> command(s) -> paths affected.