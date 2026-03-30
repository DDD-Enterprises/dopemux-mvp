---
id: INDEX
title: Documentation Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-26'
next_review: '2026-06-26'
prelude: Canonical entrypoint for active Dopemux documentation indexes, section overviews, and automation workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Index Synchronized

# Documentation Index

Use this file as the root pointer for active documentation navigation and maintenance.

## Canonical Indexes and Lists

- [Master Index](00-MASTER-INDEX.md)
- [Machine Index](docs_index.yaml)
- [ADR Index](90-adr/adr-index.md)
- [PM Plane Hub](03-reference/planes/pm/hub.md)
- [Tutorials Overview](01-tutorials/overview.md)
- [How-To Overview](02-how-to/overview.md)
- [Reference Overview](03-reference/overview.md)
- [Explanation Overview](04-explanation/overview.md)
- [Documentation Catalog](03-reference/documentation-catalog.md)
- [PR Merge Flight Dashboard](02-how-to/pr-merge-flight-dashboard.md)
- [PR Merge Queue Orchestration](04-explanation/pr-merge-queue-orchestration.md)

## Skill Templates for Documentation Sync

- Core skill: `templates/skills/pr-docgen-sync/`
- Wrappers:
  - `templates/skills/pr-docgen-sync-gemini/`
  - `templates/skills/pr-docgen-sync-copilot/`
  - `templates/skills/pr-docgen-sync-claude/`
- PR Merge Specialist skill: `templates/skills/pr-merge-specialist/`
- Skill installer script: `scripts/skills/sync_repo_skills.py`
- Workflow kit skill pack:
  - `templates/skills/brief-drafter/`
  - `templates/skills/task-breakdown/`
  - `templates/skills/code-researcher/`
  - `templates/skills/research-reviewer/`
  - `templates/skills/implementation-planner/`
  - `templates/skills/plan-reviewer/`
  - `templates/skills/code-implementer/`
  - `templates/skills/quality-refactorer/`

## Validation Gates

Run before closing any documentation-heavy change:

```bash
bash scripts/lint-docs.sh
python scripts/docs_validator.py
python scripts/docs_frontmatter_guard.py
python scripts/check_root_hygiene.py
```
