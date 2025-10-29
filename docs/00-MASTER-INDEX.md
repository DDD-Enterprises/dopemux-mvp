# Dopemux Documentation - Master Index

**Quick Navigation:** [Getting Started](#getting-started) | [How-To Guides](#how-to) | [Systems](#systems) | [Architecture](#architecture) | [Archive](#archive)

---

## Getting Started

### New to Dopemux?
- **[Quick Start Guide](../QUICK_START.md)** - Get up and running in 5 minutes
- **[Installation](01-tutorials/START-HERE.md)** - Comprehensive setup guide
- **[README](../README.md)** - Project overview and features

---

## How-To Guides

### Deployment
- [Production Deployment](deployment/DEPLOYMENT-INSTRUCTIONS.md)
- [Docker Setup](deployment/DEPLOYMENT-CHECKLIST.md)
- [Worktree Deployment](deployment/DEPLOYMENT-WORKTREE-INSTRUCTIONS.md)

### Integrations
- [Leantime Setup](02-how-to/integrations/LEANTIME_SETUP_INSTRUCTIONS.md)
- [Leantime API Configuration](02-how-to/integrations/LEANTIME_API_SETUP_GUIDE.md)
- [MCP Server Configuration](02-how-to/metamcp-setup.md)
- [MetaMCP Quickstart](02-how-to/metamcp-quickstart.md)

### Operations
- [Role Switching](02-how-to/role-switching-quickstart.md)
- [Multi-Instance Workflow](02-how-to/multi-instance-workflow.md)
- [Instance State Persistence](02-how-to/instance-state-persistence.md)
- [Serena V2 Deployment](02-how-to/serena-v2-production-deployment.md)

---

## Systems Documentation

### ConPort System
**Location:** `systems/conport/`
- [Executive Summary](systems/conport/CONPORT_EXECUTIVE_SUMMARY.md) - Overview of ConPort systems
- [Systems Analysis](systems/conport/CONPORT_SYSTEMS_ANALYSIS.md) - Technical deep dive
- [Integration Quickstart](systems/conport/CONPORT_INTEGRATION_QUICKSTART.md)
- [Comparison Matrix](systems/conport/CONPORT_COMPARISON_MATRIX.md)
- [Full Documentation](systems/conport/CONPORT_README.md)

### Dashboard System
**Location:** `systems/dashboard/`
- [Dashboard README](systems/dashboard/TMUX_DASHBOARD_README.md)
- [Design Document](systems/dashboard/TMUX_DASHBOARD_DESIGN.md)
- [Metrics Inventory](systems/dashboard/TMUX_METRICS_INVENTORY.md)
- [Implementation Tracker](systems/dashboard/DASHBOARD_IMPLEMENTATION_TRACKER.md)
- [Enhancement Plans](systems/dashboard/DASHBOARD_ENHANCEMENTS.md)

---

## Architecture & Design

### Core Architecture
- [Architecture Overview](04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md) - Complete system architecture
- [System Bible](94-architecture/system-bible.md) - Consolidated knowledge base
- [Three-Layer Integration](90-adr/ADR-207-architecture-3.0-three-layer-integration.md)
- [Multi-Instance Implementation](94-architecture/multi-instance-implementation.md)

### Architecture Decision Records (ADRs)
**Location:** `90-adr/`
- [ADR-207: Architecture 3.0](90-adr/ADR-207-architecture-3.0-three-layer-integration.md)
- [ADR-203: Task Orchestrator](90-adr/ADR-203-task-orchestrator-un-deprecation.md)
- [ADR-202: Serena V2 Validation](90-adr/ADR-202-serena-v2-production-validation.md)
- [ADR-201: ConPort Security](90-adr/ADR-201-conport-kg-security-hardening.md)

---

## Development

### Active Planning
**Location:** `development/planning/`
- [Master Action Plan](development/planning/ACTION-PLAN-MASTER.md)
- [DDDPG Kickoff](development/planning/DDDPG_KICKOFF.md)
- [Layout Plans](development/planning/DOPE_LAYOUT_MODULAR_PLAN.md)

### Implementation Plans
**Location:** `implementation-plans/`
- [Master Index](implementation-plans/00-MASTER-INDEX.md)
- [Dashboard Implementation](implementation-plans/DASHBOARD_IMPLEMENTATION_TRACKER.md)
- [ConPort HTTP Planning](implementation-plans/CONPORT_HTTP_DEEP_PLANNING.md)
- [Component Summaries](implementation-plans/component-1-audit-summary.md)

---

## Reference

### Configuration
- [Profile YAML Schema](PROFILE-YAML-SCHEMA.md)
- [MetaMCP Tool Mapping](03-reference/metamcp-tool-mapping.md)

### Features
- [Features Index](FEATURES_INDEX.md)
- [Untracked Work Detection](03-reference/F001-ENHANCED-untracked-work-system.md)
- [Multi-Session Support](03-reference/F002-multi-session-support.md)

### Technical Deep Dives
- [Serena V2 Technical Deep Dive](04-explanation/serena-v2-technical-deep-dive.md)
- [ConPort Technical Deep Dive](04-explanation/conport-technical-deep-dive.md)

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
2. **How-To** (`02-how-to/`) - Problem-oriented step-by-step instructions
3. **Reference** (`03-reference/`) - Technical specifications and API docs
4. **Explanation** (`04-explanation/`) - Understanding-oriented architecture docs
5. **Systems** (`systems/`) - Component-specific documentation hubs
6. **Design** (`90-adr/`, `91-rfc/`) - Architecture decisions and proposals
7. **Development** (`development/`, `implementation-plans/`) - Active development docs
8. **Archive** (`archive/`) - Historical records and completed work

---

## Contributing to Documentation

When adding new documentation:

1. **Choose the right location:**
   - Tutorials: Step-by-step learning paths
   - How-To: Solving specific problems
   - Reference: Technical specs, APIs, schemas
   - Explanation: Concepts, architecture, design rationale
   - Systems: Feature/component-specific docs

2. **File naming:**
   - Use `kebab-case.md` for new files
   - Prefix ADRs: `ADR-NNN-title.md`
   - Prefix RFCs: `RFC-NNN-title.md`

3. **Update indexes:**
   - Add entry to this master index
   - Update relevant section README
   - Link from related documents

---

**Last Updated:** 2025-10-29
**Maintainer:** Documentation reorganization complete
