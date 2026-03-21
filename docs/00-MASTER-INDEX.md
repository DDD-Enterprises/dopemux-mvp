---
id: 00-MASTER-INDEX
title: 00 Master Index
type: explanation
owner: '@hu3mann'
last_review: '2026-03-19'
next_review: '2026-06-19'
author: '@hu3mann'
date: '2026-02-05'
prelude: 00 Master Index (explanation) for dopemux documentation and developer workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Topology Complete

# Dopemux Documentation - Master Index

**Quick Navigation:** [Getting Started](#getting-started) | [How-To Guides](#how-to) | [Systems](#systems) | [Architecture](#architecture) | [Research Progress](04-explanation/technical-deep-dives/research-leaderboard.md) | [Archive](#archive)

---

## Getting Started

### New to Dopemux?
- **[Quick Start Guide](../QUICK_START.md)** - Get up and running in 5 minutes
- **[Installation](01-tutorials/start-here-2.md)** - Comprehensive setup guide
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
- [Internal Workflow Kit](02-how-to/internal-workflow-kit.md)
- [Workflow Idea to Epic Lifecycle](02-how-to/operations/workflow-idea-epic-lifecycle.md)
- [Serena V2 Deployment](02-how-to/serena-v2-production-deployment.md)
- [Repo Truth Extractor CLI Runbook](02-how-to/extraction/run-v4-from-dopemux-cli.md) - canonical command namespace: `dopemux upgrades ...` (`extractor` is legacy alias)
- [Repo Truth Extractor User Guide](02-how-to/extraction/repo-truth-extractor-user-guide.md)
- [Repo Truth Extractor Batch Quickstart](02-how-to/extraction/batch-quickstart.md)
- [Repo Truth Extractor Reference](03-reference/extraction/pipeline-reliability.md)
- [Repo Truth Extractor Phase Map](03-reference/extraction/pipeline-phases.md)
- [Dope-Context User Guide](02-how-to/dope-context/dope-context-user-guide.md)

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

---

## Architecture & Design

### Core Architecture
- [Architecture Overview](04-explanation/architecture/dopemux-architecture-overview-2.md) - Complete system architecture
- [System Bible](04-explanation/architecture/system-bible.md) - Consolidated knowledge base
- [Three-Layer Integration](90-adr/adr-207-architecture-3-0-three-layer-integration.md)
- [Multi-Instance Implementation](04-explanation/architecture/multi-instance-implementation.md)
- [Canonical Compose Runtime](../compose.yml) - Single orchestration source for smoke + full-stack operations

### Architecture Decision Records (ADRs)
**Location:** `90-adr/`
- [ADR Index](90-adr/adr-index.md)
- [ADR-207: Architecture 3.0](90-adr/adr-207-architecture-3-0-three-layer-integration.md)
- [ADR-203: Task Orchestrator](90-adr/adr-203-task-orchestrator-un-deprecation-2.md)
- [ADR-202: Serena V2 Validation](90-adr/adr-202-serena-v2-production-validation-2.md)
- [ADR-201: ConPort Security](90-adr/adr-201-conport-kg-security-hardening-2.md)
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
- [PM Plane Write Adjudication Model](planes/pm/pm-plane-write-adjudication-model.md)
- [PM Plane Write Matrix](planes/pm/pm-plane-write-matrix.md)
- [PM Plane Normalized Tool Surface](planes/pm/pm-plane-normalized-tool-surface.md)
- [PM Plane Read Matrix](planes/pm/pm-plane-read-matrix.md)
- [PM Plane Write Surface Policy](planes/pm/pm-plane-write-surface-policy.md)

---

## Development

### Active Planning
**Location:** `archive/development/planning/`
- [Master Action Plan](archive/development/planning/action-plan-master-2.md)
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
- Skill install/sync script: `scripts/skills/sync_repo_skills.py`

---

## Reference

### Configuration
- [Profile YAML Schema](03-reference/configuration/profile-yaml-schema-2.md)
- [MCP Tools Overview](03-reference/mcp-tools-overview.md)
- [Task Orchestrator Service Reference](03-reference/services/task-orchestrator.md)
- [Dope-Context Docs Contextual Embedding Contract](03-reference/dope-context/dope-context-docs-contextual-embedding-v1.md)
- [Dope-Context Architecture and Trinity Boundaries](03-reference/dope-context/dope-context-architecture-and-boundaries-v1.md)
- [Internal Workflow Kit Reference](03-reference/internal-workflow-kit.md)

### Features
- [Features Index](03-reference/features/features-index.md)
- [Untracked Work Detection](03-reference/f001-enhanced-untracked-work-system-2.md)
- [Multi-Session Support](03-reference/f002-multi-session-support-2.md)

### Governance
- [Authority Map](03-reference/governance/authority-map.md)
- [Conflict Ledger](03-reference/governance/conflict-ledger.md)
- Additional governance contracts are tracked in the active backlog and linked from the Authority Map.

### Technical Deep Dives
- [Serena V2 Technical Deep Dive](04-explanation/technical-deep-dives/serena-v2-technical-deep-dive.md)
- [ConPort Technical Deep Dive](04-explanation/technical-deep-dives/conport-technical-deep-dive.md)
- [Dope-Memory Deep Dive](04-explanation/technical-deep-dives/dope-memory-deep-dive-2.md)
- [ADHD Engine Deep Dive](04-explanation/technical-deep-dives/adhd-engine-deep-dive-part1-2.md)
- [Dopemux Context Deep Dive](04-explanation/technical-deep-dives/dopemux-context-deep-dive-2.md)
- [Workflow Kit Architecture](04-explanation/workflow-kit-architecture.md)

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

This documentation follows a hybrid approach:

1. **Getting Started** (`01-tutorials/`) - Learning-oriented guides for newcomers
1. **How-To** (`02-how-to/`) - Problem-oriented step-by-step instructions
1. **Reference** (`03-reference/`) - Technical specifications and API docs
1. **Explanation** (`04-explanation/`) - Understanding-oriented architecture docs
1. **Systems** (`systems/`) - Component-specific documentation hubs
1. **Design** (`90-adr/`, `91-rfc/`) - Architecture decisions and proposals
1. **Development** (`development/`, `implementation-plans/`) - Active development docs
1. **Archive** (`archive/`) - Historical records and completed work

---

## Contributing to Documentation

When adding new documentation:

1. **Choose the right location:**
- Tutorials: Step-by-step learning paths
- How-To: Solving specific problems
- Reference: Technical specs, APIs, schemas
- Explanation: Concepts, architecture, design rationale
- Systems: Feature/component-specific docs

1. **File naming:**
- Use `kebab-case.md` for new files
- Prefix ADRs: `ADR-NNN-title.md`
- Prefix RFCs: `RFC-NNN-title.md`

1. **Update indexes:**
- Add entry to this master index
- Update relevant section README
- Link from related documents

---

**Last Updated:** 2026-03-11
**Maintainer:** Documentation reorganization complete
