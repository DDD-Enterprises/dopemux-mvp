---
id: DOCUMENTATION-CATALOG
title: Documentation Catalog
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-11'
prelude: Canonical catalog of active documentation indexes, policy files, and documentation automation entrypoints.
---
# Documentation Catalog

## Canonical Active Index Surfaces

- `docs/docs_index.yaml`
- `docs/00-MASTER-INDEX.md`
- `docs/INDEX.md`
- `docs/01-tutorials/overview.md`
- `docs/02-how-to/overview.md`
- `docs/03-reference/overview.md`
- `docs/04-explanation/overview.md`

## Documentation Automation

- Core PR doc sync skill template: `templates/skills/pr-docgen-sync/`
- Wrapper templates:
  - `templates/skills/pr-docgen-sync-gemini/`
  - `templates/skills/pr-docgen-sync-copilot/`
  - `templates/skills/pr-docgen-sync-claude/`
- PR merge queue skill template: `templates/skills/pr-merge-specialist/` with packaged tests, bundled policy, and phase-oriented queue orchestration
- Skill sync installer: `scripts/skills/sync_repo_skills.py`
- Legacy compatibility sync: `scripts/skills/sync_testgen_skills.py`

## Required Validation Commands

```bash
python scripts/docs_validator.py
python scripts/docs_frontmatter_guard.py
python scripts/check_root_hygiene.py
```

## Placement Policy

Active docs are maintained in Diataxis-aligned folders under `docs/`.

Exclude these trees from mandatory active index reconciliation unless directly touched:
- `docs/archive/**`
- `docs/04-explanation/history/**`
