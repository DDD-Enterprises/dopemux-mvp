# Build and Self-Check

## Reproducible Build Steps

```bash
python scripts/skills/sync_repo_skills.py --family pr-merge-specialist
PYTHONPATH=templates/skills/pr-merge-specialist/scripts python -m dopemux_pr_merge_specialist.cli self-check --out-dir proof/pr_merge
PYTHONPATH=templates/skills/pr-merge-specialist/scripts pytest -q templates/skills/pr-merge-specialist/tests
```

## Packaging Rules

- Include the files listed in `PACKAGE_MANIFEST.json`.
- Exclude `__pycache__/`, `*.pyc`, and `__MACOSX/`.
- Validate the packaged skill from the installed form, not only from the repo source tree.
