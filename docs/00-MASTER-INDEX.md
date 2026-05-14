---
id: 00-MASTER-INDEX
title: 00 Master Index
type: explanation
owner: '@hu3mann'
last_review: '2026-04-12'
next_review: '2026-06-30'
author: '@hu3mann'
date: '2026-02-05'
prelude: 00 Master Index (explanation) for dopemux documentation and developer workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Topology Complete

# Dopemux Documentation - Master Index

**Quick Navigation:** [Getting Started](#getting-started) | [How-To Guides](#how-to) | [Systems](#systems-documentation) | [Architecture](#architecture--design) | [Research Progress](04-explanation/technical-deep-dives/research-leaderboard.md) | [Archive](#archive)

---

## Getting Started

### New to Dopemux?
- **[Quick Start Guide](../QUICK_START.md)** - Get up and running in 5 minutes
- **[Installation](01-tutorials/start-here.md)** - Comprehensive setup guide
- **[README](../README.md)** - Project overview and features

---

## How-To Guides

### ADHD Features
- **[ADHD Features User Guide](02-how-to/adhd-features-user-guide.md)** - Complete guide to all 11 cognitive features
- **[ADHD Quick Reference](02-how-to/adhd-features-quick-reference.md)** - Quick command reference card
- **[ADHD Engine API](03-reference/adhd-engine-api.md)** - Full API documentation

### Deployment
- [Production Deployment](02-how-to/deployment-guide.md)
- [Docker Setup](02-how-to/deployment-guide.md)
- [Worktree Deployment](02-how-to/deployment-worktree.md)

### Integrations
- [Leantime Setup](02-how-to/integrations/leantime-integration-guide.md)
- [Leantime API Configuration](02-how-to/integrations/leantime-integration-guide.md)
- [MCP Service Discovery Guide](02-how-to/mcp-service-discovery-guide.md)
- [MCP Tools Overview](03-reference/mcp-tools-overview.md)

### Operations
- [Role Switching](02-how-to/role-switching-quickstart.md)
- [Multi-Instance Workflow](02-how-to/multi-instance-workflow.md)
- [Instance State Persistence](02-how-to/instance-state-persistence.md)
- [Orchestrator Dashboard Quickstart](02-how-to/orchestrator-dashboard.md)
- [PR Merge Flight Dashboard Quickstart](02-how-to/pr-merge-flight-dashboard.md)
- [CI Remediation Specialist Reference](03-reference/ci-remediation-specialist.md)
- [Internal Workflow Kit](02-how-to/internal-workflow-kit.md)
- [Workflow Idea to Epic Lifecycle](02-how-to/operations/workflow-idea-epic-lifecycle.md)
- [Serena V2 Deployment](02-how-to/serena-v2-production-deployment.md)
- [Repo Truth Extractor CLI Runbook](02-how-to/extraction/run-v4-from-dopemux-cli.md) - canonical command namespace: `dopemux rte ...` (`upgrades` is a legacy compatibility alias; `extractor` is a hidden legacy/refusal surface)
- [Repo Truth Extractor User Guide](02-how-to/extraction/repo-truth-extractor-user-guide.md)
- [Repo Truth Extractor v5 First Live Run](02-how-to/extraction/repo-truth-extractor-v5-first-live-run.md)
- [Repo Truth Extractor Truth-Run Command](02-how-to/extraction/truth-run-command.md)
- [Repo Truth Extractor Batch Quickstart](02-how-to/extraction/batch-quickstart.md)
- [Repo Truth Extractor Reference](03-reference/extraction/pipeline-reliability.md)
- [Repo Truth Extractor Phase Map](03-reference/extraction/pipeline-phases.md)
- [Repo Truth Extractor v5 Upgrade Design](04-explanation/architecture/v5-extraction-pipeline-upgrade-design.md)
- [Dope-Context User Guide](02-how-to/dope-context/dope-context-user-guide.md)
- [PR Merge Flight Dashboard](02-how-to/pr-merge-flight-dashboard.md) - Canonical operator quickstart for `dopemux pr-merge flight` and `dopemux-pr-merge flight`

---

## Systems Documentation

### ConPort System
**Location:** `03-reference/systems/conport/`
- [Executive Summary](03-reference/systems/conport/conport-kg-status.md) - Current ConPort status and quick overview
- [Systems Analysis](04-explanation/technical-deep-dives/conport-technical-deep-dive.md) - Technical deep dive
- [Integration Quickstart](02-how-to/mcp-service-discovery-guide.md)
- [Comparison Matrix](05-audit-reports/service-maturity-gap-analysis.md)
- [Full Documentation](03-reference/systems/conport/conport-kg-status.md)
- [Callable Surface Inventory](systems/conport/callable-surface-inventory.md)
- [Surface Equivalence and Drift](systems/conport/surface-equivalence-and-drift.md)
- [Preferred Canonical Surface](systems/conport/preferred-canonical-surface.md)
- [Authority Invariants and Dark Methods](systems/conport/authority-invariants-and-dark-methods.md)

### Dashboard System
**Location:** `03-reference/systems/dashboard/`
- [Dashboard README](03-reference/systems/dashboard/tmux-dashboard-readme.md)
- [Design Document](03-reference/systems/dashboard/tmux-dashboard-design.md)
- [Metrics Inventory](03-reference/systems/dashboard/tmux-metrics-inventory.md)
- [Implementation Tracker](03-reference/systems/dashboard/dashboard-implementation-tracker.md)
- [Enhancement Plans](03-reference/systems/dashboard/dashboard-enhancements.md)

### Execution Plane System
**Location:** `docs/planes/execution/`
- **[Agent Leasing Contract](planes/execution/agent-leasing-contract.md)** - Authoritative "Rules of Engagement" for AI agent execution, heartbeats, and handoffs.

---

## Architecture & Design

### Core Architecture
- [Architecture Overview](04-explanation/architecture/dopemux-architecture-overview.md) - Complete system architecture
- [Full Codebase Explainer](04-explanation/architecture/dopemux-mvp-full-codebase-explainer.md) - Repo-truth explainer for the active Dopemux control surfaces, service boundaries, and authority split
- [System Bible](04-explanation/architecture/system-bible.md) - Consolidated knowledge base
- [Three-Layer Integration](90-adr/adr-207-architecture-3-0-three-layer-integration.md)
- [Multi-Instance Implementation](04-explanation/architecture/multi-instance-implementation.md)
- [Canonical Compose Runtime](../compose.yml) - Single orchestration source for smoke + full-stack operations
- [PR Merge Queue Orchestration](04-explanation/pr-merge-queue-orchestration.md) - Queue-state, validation, and remediation rationale for the PR merge specialist

### Architecture Decision Records (ADRs)
**Location:** `90-adr/`
- [ADR Index](90-adr/adr-index.md)
- [ADR-207: Architecture 3.0](90-adr/adr-207-architecture-3-0-three-layer-integration.md)
- [ADR-203: Task Orchestrator](90-adr/adr-203-task-orchestrator-un-deprecation.md)
- [ADR-202: Serena V2 Validation](90-adr/adr-202-serena-v2-production-validation.md)
- [ADR-201: ConPort Security](90-adr/adr-201-conport-kg-security-hardening.md)
- [ADR: PM Plane Authority Boundaries](90-adr/adr-pm-plane-authority-boundaries.md)
- [ADR: ConPort Decision/Progress/Context Authority](90-adr/adr-conport-as-decision-progress-and-context-authority.md)
- [ADR: dope-memory Chronicle Memory Authority](90-adr/adr-dope-memory-as-chronicle-memory-authority.md)
- [ADR: Dopecon-Bridge Adapter-Only Scope](90-adr/adr-dopecon-bridge-narrowing-to-adapter-only-role.md)
- [ADR: Leantime JSON-RPC + Plugin Integration Strategy](90-adr/adr-leantime-json-rpc-plus-plugin-integration-strategy.md)
- [ADR: Task Orchestrator Workflow Authority](90-adr/adr-task-orchestrator-as-workflow-authority.md)
- [ADR: Memory Trinity Authority and Interaction Model](90-adr/adr-memory-trinity-authority-and-interaction-model.md)
- [ADR: Serena Technical Context Plane](90-adr/adr-serena-as-technical-context-plane.md)
- [ADR: dope-context Search and Retrieval Plane](90-adr/adr-dope-context-as-search-and-retrieval-plane.md)

### PM Plane Contracts
**Location:** `planes/pm/`
- [PM Plane Hub](planes/pm/hub-2.md)
- [PM Plane Evidence Hub](planes/pm/readme-2.md)
- [PM Plane Write Adjudication Model](planes/pm/pm-plane-write-adjudication-model.md)
- [PM Plane Write Matrix](planes/pm/pm-plane-write-matrix.md)
- [PM Plane Normalized Tool Surface](planes/pm/pm-plane-normalized-tool-surface.md)
- [PM Plane Read Matrix](planes/pm/pm-plane-read-matrix.md)
- [PM Plane Write Surface Policy](planes/pm/pm-plane-write-surface-policy.md)
- [Supervisor PM and Memory MCP Server Matrix](05-audit-reports/supervisor-pm-mcp-server-matrix-2026-03-27.md)
- [Supervisor PM and Memory Evidence Packet](05-audit-reports/supervisor-pm-evidence-packet-2026-03-27.md)
- [Supervisor Memory and PM Authority Reconciliation](05-audit-reports/supervisor-memory-pm-authority-reconciliation-2026-03-27.md)
- [Supervisor PM and Memory Authority Enforcement Packet](05-audit-reports/supervisor-pm-memory-authority-enforcement-packet-2026-04-01.md)
- Runtime-truth executive summaries:
  - [Task Orchestrator](planes/pm/_evidence/task-orchestrator-runtime-truth/executive-summary.md)
  - [Leantime](planes/pm/_evidence/leantime-runtime-truth/executive-summary.md)
  - [dopecon-bridge](planes/pm/_evidence/dopecon-bridge-runtime-truth/executive-summary.md)

---

## Development

### Active Planning
**Location:** `archive/development/planning/`
- [Master Action Plan](archive/development/planning/ACTION-PLAN-MASTER.md)
- [DDDPG Kickoff](archive/development/planning/dddpg-kickoff.md)
- [Layout Plans](archive/development/planning/dope-layout-modular-plan.md)

### Implementation Plans
**Location:** `archive/implementation-plans/`
- [Master Index](archive/implementation-plans/00-master-index-2.md)
- [Dashboard Implementation](archive/implementation-plans/dashboard-implementation-tracker.md)
- [ConPort HTTP Planning](archive/implementation-plans/conport-http-deep-planning.md)
- [Component Summaries](archive/implementation-plans/component-1-audit-summary.md)

### Documentation Automation
- [Documentation Root Index](INDEX.md)
- [Documentation Catalog](03-reference/documentation-catalog.md)
- PR Docgen Sync skill templates:
  - `templates/skills/pr-docgen-sync/`
  - `templates/skills/pr-docgen-sync-gemini/`
  - `templates/skills/pr-docgen-sync-copilot/`
  - `templates/skills/pr-docgen-sync-claude/`
- PR Merge Specialist skill template:
  - `templates/skills/pr-merge-specialist/`
- Skill install/sync script: `scripts/skills/sync_repo_skills.py`

---

## Reference

### Configuration
- [Profile YAML Schema](03-reference/configuration/profile-yaml-schema.md)
- [MCP Tools Overview](03-reference/mcp-tools-overview.md)
- [Dopemux Hooksd](03-reference/services/dopemux-hooksd.md)
- [Task Orchestrator Service Reference](03-reference/services/task-orchestrator.md)
- [Dope-Context Docs Contextual Embedding Contract](03-reference/dope-context/dope-context-docs-contextual-embedding-v1.md)
- [Dope-Context Architecture and Trinity Boundaries](03-reference/dope-context/dope-context-architecture-and-boundaries-v1.md)
- [Internal Workflow Kit Reference](03-reference/internal-workflow-kit.md)
- [CI Remediation Specialist Reference](03-reference/ci-remediation-specialist.md)

### Features
- [Features Index](03-reference/features/features-index.md)
- [Untracked Work Detection](03-reference/f001-enhanced-untracked-work-system.md)
- [Multi-Session Support](03-reference/f002-multi-session-support.md)

### Governance
- [Authority Map](03-reference/governance/authority-map.md)
- [Conflict Ledger](03-reference/governance/conflict-ledger.md)
- Additional governance contracts are tracked in the active backlog and linked from the Authority Map.

### Technical Deep Dives
- [Memory And Persistence Deep Dive](04-explanation/technical-deep-dives/memory-and-persistence-deep-dive.md)
- [Repo Truth Extractor — Structure, Architecture & Optimal Design](04-explanation/technical-deep-dives/repo-truth-extractor-structure-architecture-and-optimal-design.md)
- [Serena V2 Technical Deep Dive](04-explanation/technical-deep-dives/serena-v2-technical-deep-dive.md)
- [ConPort Technical Deep Dive](04-explanation/technical-deep-dives/conport-technical-deep-dive.md)
- [Dope-Memory Deep Dive](04-explanation/technical-deep-dives/dope-memory-deep-dive-2.md)
- [ADHD Engine Deep Dive](04-explanation/technical-deep-dives/adhd-engine-deep-dive-part1-2.md)
- [Dopemux Context Deep Dive](04-explanation/technical-deep-dives/dopemux-context-deep-dive-2.md)
- [Workflow Kit Architecture](04-explanation/workflow-kit-architecture.md)
- [PR Merge Queue Orchestration](04-explanation/pr-merge-queue-orchestration.md)

### RFCs
- [Workflow Kit Pickle Mechanics Transfer](91-rfc/workflow-kit-pickle-mechanics-transfer.md)

---

## Archive

### Completed Projects
**Location:** `archive/completed-projects/`

Recent completions:
- ConPort Event Bridge Integration
- LSP Hover Feature
- Production Deployment
- Leantime MCP Integration
- Security Audit & Fixes
- Multi-Instance Workspace Fix

### Session Notes
**Location:** `archive/session-notes/2025-10/`

Historical session summaries and sprint notes.

### Deprecated Documentation
**Location:** `archive/deprecated/`

Outdated or superseded documentation kept for reference.

---

## Document Organization

This documentation follows the [Diataxis](https://diataxis.fr/) framework:

1. **Tutorials** (`01-tutorials/`) - Learning-oriented guides for newcomers
1. **How-To** (`02-how-to/`) - Problem-oriented step-by-step instructions
1. **Reference** (`03-reference/`) - Technical specifications, API docs, systems, and planes
   - `03-reference/systems/` - Component-specific documentation hubs
   - `03-reference/planes/` - Plane contracts and authority boundaries
1. **Explanation** (`04-explanation/`) - Understanding-oriented architecture docs
1. **Design** (`90-adr/`, `91-rfc/`) - Architecture decisions and proposals
1. **Runbooks** (`92-runbooks/`) - Operational runbooks
1. **Archive** (`archive/`) - Historical records, completed work, and legacy docs
   - `archive/development/planning/` - Historical planning docs
   - `archive/implementation-plans/` - Historical implementation plans

---

## Contributing to Documentation

See [docs/03-reference/contributing.md](03-reference/contributing.md) for the full documentation standards and contribution guide.

Quick reference:

1. **Choose the right location:**
   - Tutorials: Step-by-step learning paths
   - How-To: Solving specific problems
   - Reference: Technical specs, APIs, schemas, systems, planes
   - Explanation: Concepts, architecture, design rationale

1. **File naming:**
   - Use `kebab-case.md` for new files
   - Prefix ADRs: `adr-NNN-title.md`
   - Prefix RFCs: `rfc-NNN-title.md`
   - Never create `-2`/`-3` suffix copies — use git for versioning

1. **Update indexes:**
   - Add entry to this master index
   - Update relevant section README
   - Link from related documents

1. **Validate:**
   - Run `bash scripts/lint-docs.sh` after doc changes

---

**Last Updated:** 2026-03-27
**Maintainer:** Documentation reorganization complete
