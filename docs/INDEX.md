---
id: INDEX
title: Documentation Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-11'
prelude: Canonical entrypoint for active Dopemux documentation indexes, section overviews, and automation workflows.
---
# Documentation Index

Use this file as the root pointer for active documentation navigation and maintenance.

## Canonical Indexes and Lists

- [Master Index](00-MASTER-INDEX.md)
- [Machine Index](docs_index.yaml)
- [ADR Index](90-adr/adr-index.md)
- [PM Plane Hub](planes/pm/hub-2.md)
- [Tutorials Overview](01-tutorials/overview.md)
- [How-To Overview](02-how-to/overview.md)
- [Reference Overview](03-reference/overview.md)
- [Explanation Overview](04-explanation/overview.md)
- [Documentation Catalog](03-reference/documentation-catalog.md)

## Skill Templates for Documentation Sync

- Core skill: `templates/skills/pr-docgen-sync/`
- Wrappers:
  - `templates/skills/pr-docgen-sync-gemini/`
  - `templates/skills/pr-docgen-sync-copilot/`
  - `templates/skills/pr-docgen-sync-claude/`
- Skill installer script: `scripts/skills/sync_repo_skills.py`

## Validation Gates

Run before closing any documentation-heavy change:

```bash
python scripts/docs_validator.py
python scripts/docs_frontmatter_guard.py
python scripts/check_root_hygiene.py
```
