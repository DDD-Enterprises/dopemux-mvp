---
id: 00-MASTER-INDEX
title: 00 Master Index
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: 00 Master Index (explanation) for dopemux documentation and developer workflows.
---
# Dopemux Documentation - Master Index

**Quick Navigation:** [Getting Started](#getting-started) | [How-To Guides](#how-to) | [Systems](#systems) | [Architecture](#architecture) | [Research Progress](04-explanation/technical-deep-dives/RESEARCH_LEADERBOARD.md) | [Archive](#archive)

---

## Getting Started

### New to Dopemux?
- **[Quick Start Guide](../QUICK_START.md)** - Get up and running in 5 minutes
- **[Installation](01-tutorials/START-HERE.md)** - Comprehensive setup guide
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
- [Workflow Idea to Epic Lifecycle](02-how-to/operations/workflow-idea-epic-lifecycle.md)
- [Serena V2 Deployment](02-how-to/serena-v2-production-deployment.md)
- [Repo Truth Extractor CLI Runbook](02-how-to/extraction/run-v4-from-dopemux-cli.md) - canonical command namespace: `dopemux upgrades ...` (`extractor` is legacy alias)
- [Repo Truth Extractor User Guide](02-how-to/extraction/repo-truth-extractor-user-guide.md)
- [Repo Truth Extractor Batch Quickstart](02-how-to/extraction/batch-quickstart.md)
- [Repo Truth Extractor Reference](03-reference/extraction/pipeline-reliability.md)
- [Repo Truth Extractor Phase Map](03-reference/extraction/pipeline-phases.md)

---

## Systems Documentation

### ConPort System
**Location:** `03-reference/systems/conport/`
- [Executive Summary](03-reference/systems/conport/conport-kg-status.md) - Current ConPort status and quick overview
- [Systems Analysis](04-explanation/technical-deep-dives/conport-technical-deep-dive.md) - Technical deep dive
- [Integration Quickstart](02-how-to/mcp-service-discovery-guide.md)
- [Comparison Matrix](05-audit-reports/service-maturity-gap-analysis.md)
- [Full Documentation](03-reference/systems/conport/conport-kg-status.md)

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
- [Architecture Overview](04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md) - Complete system architecture
- [System Bible](04-explanation/architecture/system-bible.md) - Consolidated knowledge base
- [Three-Layer Integration](90-adr/ADR-207-architecture-3.0-three-layer-integration.md)
- [Multi-Instance Implementation](04-explanation/architecture/multi-instance-implementation.md)

### Architecture Decision Records (ADRs)
**Location:** `90-adr/`
- [ADR-207: Architecture 3.0](90-adr/ADR-207-architecture-3.0-three-layer-integration.md)
- [ADR-203: Task Orchestrator](90-adr/ADR-203-task-orchestrator-un-deprecation.md)
- [ADR-202: Serena V2 Validation](90-adr/ADR-202-serena-v2-production-validation.md)
- [ADR-201: ConPort Security](90-adr/ADR-201-conport-kg-security-hardening.md)

---

## Development

### Active Planning
**Location:** `archive/development/planning/`
- [Master Action Plan](archive/development/planning/ACTION-PLAN-MASTER.md)
- [DDDPG Kickoff](archive/development/planning/DDDPG_KICKOFF.md)
- [Layout Plans](archive/development/planning/DOPE_LAYOUT_MODULAR_PLAN.md)

### Implementation Plans
**Location:** `archive/implementation-plans/`
- [Master Index](archive/implementation-plans/00-MASTER-INDEX.md)
- [Dashboard Implementation](archive/implementation-plans/DASHBOARD_IMPLEMENTATION_TRACKER.md)
- [ConPort HTTP Planning](archive/implementation-plans/CONPORT_HTTP_DEEP_PLANNING.md)
- [Component Summaries](archive/implementation-plans/component-1-audit-summary.md)

---

## Reference

### Configuration
- [Profile YAML Schema](03-reference/configuration/PROFILE-YAML-SCHEMA.md)
- [MCP Tools Overview](03-reference/mcp-tools-overview.md)
- [Task Orchestrator Service Reference](03-reference/services/task-orchestrator.md)

### Features
- [Features Index](03-reference/features/features-index.md)
- [Untracked Work Detection](03-reference/F001-ENHANCED-untracked-work-system.md)
- [Multi-Session Support](03-reference/F002-multi-session-support.md)

### Governance
- [Authority Map](03-reference/governance/AUTHORITY_MAP.md)
- [Conflict Ledger](03-reference/governance/CONFLICT_LEDGER.md)
- [CI Contract](03-reference/governance/CI_CONTRACT.md)
- [Runtime Contract](03-reference/governance/RUNTIME_CONTRACT.md)
- [Scoreboard](03-reference/governance/SCOREBOARD.md)
- [Task Packet Standard](03-reference/governance/TASK_PACKET_STANDARD.md)
- [Task Packet Template](03-reference/governance/TASK_PACKET_TEMPLATE.md)

### Technical Deep Dives
- [Serena V2 Technical Deep Dive](04-explanation/technical-deep-dives/serena-v2-technical-deep-dive.md)
- [ConPort Technical Deep Dive](04-explanation/technical-deep-dives/conport-technical-deep-dive.md)
- [Dope-Memory Deep Dive](04-explanation/technical-deep-dives/DOPE-MEMORY-DEEP-DIVE.md)
- [ADHD Engine Deep Dive](04-explanation/technical-deep-dives/ADHD-ENGINE-DEEP-DIVE-PART1.md)
- [Dopemux Context Deep Dive](04-explanation/technical-deep-dives/DOPEMUX-CONTEXT-DEEP-DIVE.md)

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

**Last Updated:** 2025-10-29
**Maintainer:** Documentation reorganization complete
