# Contributing to Dopemux MVP

Thanks for contributing to Dopemux.

## Development Setup

1. Fork and clone the repository.
2. Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
pre-commit install --install-hooks
```

3. Start a local stack for validation:

```bash
docker compose -f docker-compose.smoke.yml up --build -d
```

## Branching and Pull Requests

1. Create a feature branch from `main`.
2. Keep changes scoped and auditable.
3. Open a pull request with:
   - clear problem statement
   - summary of changes
   - test evidence
   - rollback notes for risky changes

Use the repository PR template and complete all checklist items.

## Required Checks Before PR

Run these locally before opening or updating a PR:

```bash
python scripts/check_root_hygiene.py --all-files
pytest tests/unit --maxfail=1 --disable-warnings --no-cov
./test_installer_basic.sh
```

If you changed workflows, also run actionlint or equivalent workflow linting.

## Documentation Requirements

Update docs with code changes when behavior, interfaces, or operations change:

- `README.md` for user-facing entrypoints
- `INSTALL.md` and `QUICK_START.md` for onboarding/runtime changes
- architecture docs under `docs/` for structural changes

## Security

Do not open public issues for vulnerabilities. Follow `SECURITY.md` for reporting.
