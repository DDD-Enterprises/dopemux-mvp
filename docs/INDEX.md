---
id: INDEX
title: Documentation Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-19'
last_review: '2026-03-19'
next_review: '2026-06-19'
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
- [PM Plane Hub](planes/pm/hub-2.md)
- [Tutorials Overview](01-tutorials/overview.md)
- [How-To Overview](02-how-to/overview.md)
- [Reference Overview](03-reference/overview.md)
- [Explanation Overview](04-explanation/overview.md)
- [Documentation Catalog](03-reference/documentation-catalog.md)
- [Internal Workflow Kit How-To](02-how-to/internal-workflow-kit.md)
- [Internal Workflow Kit Reference](03-reference/internal-workflow-kit.md)
- [Workflow Kit Architecture](04-explanation/workflow-kit-architecture.md)
- [Workflow Kit Transfer RFC](91-rfc/workflow-kit-pickle-mechanics-transfer.md)

## Skill Templates for Documentation Sync

- Core skill: `templates/skills/pr-docgen-sync/`
- Wrappers:
  - `templates/skills/pr-docgen-sync-gemini/`
  - `templates/skills/pr-docgen-sync-copilot/`
  - `templates/skills/pr-docgen-sync-claude/`
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
python scripts/docs_validator.py
python scripts/docs_frontmatter_guard.py
python scripts/check_root_hygiene.py
```
