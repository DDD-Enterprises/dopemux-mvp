---
id: DOCUMENTATION-CATALOG
title: Documentation Catalog
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-19'
last_review: '2026-03-19'
next_review: '2026-06-19'
prelude: Canonical catalog of active documentation indexes, policy files, and documentation automation entrypoints.
---
# Documentation Catalog

## Canonical Active Index Surfaces

- `docs/docs_index.yaml`
- `docs/00-MASTER-INDEX.md`
- `docs/INDEX.md`
- `docs/90-adr/adr-index.md`
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
- Skill sync installer: `scripts/skills/sync_repo_skills.py`
- Legacy compatibility sync: `scripts/skills/sync_testgen_skills.py`

## Workflow Kit Active Surfaces

- `docs/02-how-to/internal-workflow-kit.md`
- `docs/03-reference/internal-workflow-kit.md`
- `docs/04-explanation/workflow-kit-architecture.md`
- `docs/91-rfc/workflow-kit-pickle-mechanics-transfer.md`
- `templates/skills/brief-drafter/`
- `templates/skills/task-breakdown/`
- `templates/skills/code-researcher/`
- `templates/skills/research-reviewer/`
- `templates/skills/implementation-planner/`
- `templates/skills/plan-reviewer/`
- `templates/skills/code-implementer/`
- `templates/skills/quality-refactorer/`

## Supervisor Authority Packet Set

- `docs/05-audit-reports/supervisor-pm-mcp-server-matrix-2026-03-27.md`
- `docs/05-audit-reports/supervisor-pm-evidence-packet-2026-03-27.md`
- `docs/05-audit-reports/supervisor-memory-pm-authority-reconciliation-2026-03-27.md`
- `docs/05-audit-reports/supervisor-pm-memory-authority-enforcement-packet-2026-04-01.md`

## Required Validation Commands

```bash
python scripts/docs_validator.py
python scripts/docs_frontmatter_guard.py
python scripts/check_root_hygiene.py
```

## Placement Policy

Active docs are maintained in Diataxis-aligned folders under `docs/`.

Active subsystem and plane hubs that should be reconciled when impacted:
- `docs/planes/pm/hub-2.md`
- `docs/planes/pm/readme-2.md`
- `docs/planes/pm/_evidence/readme-3.md`

Exclude these trees from mandatory active index reconciliation unless directly touched:
- `docs/archive/**`
- `docs/04-explanation/history/**`
