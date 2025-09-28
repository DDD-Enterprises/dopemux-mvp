# CONTRIBUTING
_Last updated: 2025-09-02 UTC_

## Setup
- Python 3.11+
- `pip install -r requirements-dev.txt` (or `uv/pipx` if preferred)
- Run `pytest -q` to validate environment.

## TDD Loop
1. Pick a **Now** issue.
2. Write a failing **pytest** test from acceptance criteria.
3. Make it pass with minimal code.
4. Refactor.
5. Update docs/ADRs.
6. Commit with **Conventional Commits**.

## Commit Conventions
- `feat(scope): short summary`
- `fix(scope): short summary`
- `chore(scope): tooling/docs/etc.`
- Include `BREAKING CHANGE:` in body if necessary.

## Definition of Done
- Tests added/updated and passing
- Lint (`ruff`) and type-check (`mypy`) pass
- Docs updated (README/architecture/ADR)
- PR linked to issue
