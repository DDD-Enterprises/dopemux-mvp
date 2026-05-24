---
id: INDEX
title: Documentation Index
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-04-06'
next_review: '2026-07-06'
prelude: Canonical entrypoint for active Dopemux documentation indexes, section overviews, and automation workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Index Synchronized

# Documentation Index

Use this file as the root pointer for active documentation navigation and maintenance.

## Canonical Indexes and Lists

- [Master Index](00-MASTER-INDEX.md)
- [Machine Index](docs_index.yaml)
- [AI-Readable Map](../llms.txt)
- [ADR Index](90-adr/adr-index.md)
- [PM Plane Hub](planes/pm/hub-2.md)
- [PM Plane Evidence Hub](planes/pm/readme-2.md)
- [Tutorials Overview](01-tutorials/overview.md)
- [How-To Overview](02-how-to/overview.md)
- [Reference Overview](03-reference/overview.md)
- [Explanation Overview](04-explanation/overview.md)
- [Documentation Catalog](03-reference/documentation-catalog.md)
- [Fast Dev OS — Operational Doctrine Layer](03-reference/fast-dev-os/readme.md)
- [Fast Dev OS — Executor Prompt Pack](03-reference/fast-dev-os/prompts/readme.md)
- [Fast Dev OS — Task Packet Template (annotated)](03-reference/fast-dev-os/template-task-packet.md)
- [Fast Dev OS — PR Body Template](03-reference/fast-dev-os/template-pr-body.md)
- [Fast Dev OS — Validation Command Library](03-reference/fast-dev-os/validation-command-library.md)
- [Fast Dev OS — Runtime Dependency Cones](03-reference/fast-dev-os/runtime-dependency-cones.md)
- [Fast Dev OS — PROOF Bundle Template (templates-proof/)](03-reference/fast-dev-os/templates-proof/readme.md)
- [Root Quick Start](../QUICK_START.md)
- [Dopemux Quickstart](01-tutorials/quickstart.md)
- [Developer Onboarding](02-how-to/developer-onboarding.md)
- [Project Overview](04-explanation/overview/project-overview.md)
- [Problem Statement](04-explanation/overview/problem-statement.md)
- [System Map](04-explanation/overview/system-map.md)
- [Dopemux Architecture](04-explanation/architecture/dopemux-architecture.md)
- [Data and Control Flow](04-explanation/architecture/data-and-control-flow.md)
- [Product Positioning](04-explanation/product/positioning.md)
- [Audience Personas](04-explanation/product/audience-personas.md)
- [Homepage Copy](04-explanation/product/homepage-copy.md)
- [Public Copy Variants](04-explanation/product/public-copy-variants.md)
- [Elevator Pitches](04-explanation/product/elevator-pitches.md)
- [Features and Benefits](04-explanation/product/features-and-benefits.md)
- [Product FAQ](04-explanation/product/faq.md)
- [Repo Truth Extractor v5 First Live Run](02-how-to/extraction/repo-truth-extractor-v5-first-live-run.md)
- [Extraction Pipeline Reliability](03-reference/extraction/pipeline-reliability.md)
- [V5 Extraction Pipeline Upgrade Design](04-explanation/architecture/v5-extraction-pipeline-upgrade-design.md)
- [RTE Provider Structured Output Baseline](06-research/extraction/rte-provider-structured-output-baseline.md)
- [Supervisor PM and Memory MCP Server Matrix](05-audit-reports/supervisor-pm-mcp-server-matrix-2026-03-27.md)
- [Supervisor PM and Memory Evidence Packet](05-audit-reports/supervisor-pm-evidence-packet-2026-03-27.md)
- [Supervisor Memory and PM Authority Reconciliation](05-audit-reports/supervisor-memory-pm-authority-reconciliation-2026-03-27.md)
- [Supervisor PM and Memory Authority Enforcement Packet](05-audit-reports/supervisor-pm-memory-authority-enforcement-packet-2026-04-01.md)
- [Internal Workflow Kit How-To](02-how-to/internal-workflow-kit.md)
- [Internal Workflow Kit Reference](03-reference/internal-workflow-kit.md)
- [Workflow Kit Architecture](04-explanation/workflow-kit-architecture.md)
- [Workflow Kit Transfer RFC](91-rfc/workflow-kit-pickle-mechanics-transfer.md)
- [Dopemux Documentation Source Map](03-reference/governance/dopemux-documentation-source-map.md)
- [Documentation Gap Register](03-reference/governance/documentation-gap-register.md)
- [Documentation Trust Map](03-reference/governance/doc-trust-map.md)
- [Public Docs Surface](03-reference/governance/public-docs-surface.md)
- [Authority Boundaries](03-reference/governance/authority-boundaries.md)
- [Governance Model](03-reference/governance/governance-model.md)
- [Component Catalog](03-reference/systems/component-catalog.md)
- [Operator Workflows](02-how-to/operator-workflows.md)
- [AI Agent Handoff Guide](03-reference/instructions/ai-agent-handoff-guide.md)

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
