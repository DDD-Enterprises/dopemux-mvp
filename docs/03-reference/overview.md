---
id: README
title: Readme
type: reference
owner: '@hu3mann'
last_review: '2026-03-19'
next_review: '2026-06-19'
author: '@hu3mann'
date: '2026-02-05'
prelude: Readme (reference) for dopemux documentation and developer workflows.
---
# Reference - Technical Documentation

**Reference guides are information-oriented technical descriptions** of the machinery and how to operate it. Consult these when you need to look something up.

## Quick Navigation

- [API Documentation](#api-documentation)
- [Components](#components)
- [Configuration](#configuration)
- [Features](#features)

---

## Execution Plane

### Execution Logic & Safety
- **[Agent Leasing Contract](../planes/execution/agent-leasing-contract.md)** - Mandatory Rules of Engagement for all AI agents.

---

## API Documentation

Technical specifications for Dopemux APIs.

**Location:** `api/`

*Coming soon: API endpoint documentation, schemas, and examples*

---

## Components

Detailed reference for Dopemux components.

**Location:** `components/`

*To be organized: Component interfaces, metrics, events*

### ConPort Surface Contracts
- **[ConPort Callable Surface Inventory](../systems/conport/callable-surface-inventory.md)** - Active REST, JSON-RPC, and FastMCP surfaces
- **[ConPort Surface Equivalence and Drift](../systems/conport/surface-equivalence-and-drift.md)** - Evidence-backed surface map and drift matrix

### Workflow Kit
- **[Internal Workflow Kit Reference](internal-workflow-kit.md)** - Phases, state schema, checkpoint tokens, and role assets
- **[CI Remediation Specialist Skill](ci-remediation-specialist.md)** - Runbook, invocation contract, and queue integration

### Extraction
- **[FL INT Post-Processing](extraction/fl-int-postprocess.md)** - Standalone bounded v1 design-synthesis and feature-ledger post-pass

---

## Configuration

Configuration schemas and references.

### Configuration Files
- **[Profile YAML Schema](configuration/profile-yaml-schema.md)** - Complete profile configuration reference

### MCP Configuration
- **[MCP Tools Overview](mcp-tools-overview.md)** - MCP tool configuration and usage

### Documentation Automation
- **[Documentation Catalog](documentation-catalog.md)** - Canonical index/list surfaces and rules
- **PR Docgen Sync Skill (Core Template)** - `templates/skills/pr-docgen-sync/`
- **Gemini/Copilot/Claude Wrappers** - `templates/skills/pr-docgen-sync-*/`
- **PR Merge Specialist Skill (Template)** - `templates/skills/pr-merge-specialist/`
- **Skill Sync Script** - `scripts/skills/sync_repo_skills.py`
- **Workflow Skill Pack** - `templates/skills/{brief-drafter,task-breakdown,code-researcher,research-reviewer,implementation-planner,plan-reviewer,code-implementer,quality-refactorer}/`

### PM Plane Contracts
- **[PM Plane Write Matrix](../planes/pm/pm-plane-write-matrix.md)** - Canonical mutation writers, prechecks, mirrors, and forbidden paths
- **[PM Plane Read Matrix](../planes/pm/pm-plane-read-matrix.md)** - Canonical read sources, normalization, and provenance expectations
- **[PM Plane Write Surface Policy](../planes/pm/pm-plane-write-surface-policy.md)** - Tool classification and raw-surface exposure policy

---

## Features

Feature specifications and capabilities.

### Feature Index
- **[Features Index](features/features-index.md)** - Complete feature catalog

### Feature Specifications
- **[F001: Untracked Work Detection](f001-enhanced-untracked-work-system.md)** - Enhanced work tracking
- **[F001: Basic Untracked Work (Historical)](../archive/sessions/serena/v2/f001-usage-examples.md)** - Early implementation notes
- **[F002: Multi-Session Support](f002-multi-session-support-2.md)** - Multiple session handling
- **[PR Merge Flight Dashboard Reference](systems/dashboard/overview.md)** - Technical architecture for the PR merge TUI

### Research & Background
- **[Python Tmux Research](python-tmux-research.md)** - Technical research on tmux integration

### Test Reports
- **[Serena V2 Test Summary](../archive/test-reports/serena-v2-test-summary.md)** - ADHD engine testing archive
- **[Serena V2 Validation Report](../archive/test-reports/serena-v2-validation-report.md)** - Production validation archive

### Design Principles
- **[ADHD Theme Design Principles](adhd-theme-design-principles.md)** - UI/UX guidelines

---

## Reference Documentation Principles

Reference docs in this section:
- **Are information-oriented** - Describe the machinery
- **Are austere** - Stick to facts
- **Are consistent** - Follow standard structure
- **Are accurate** - Kept up to date with code

## Not What You're Looking For?

- **Learning how to use Dopemux?** → See [Tutorials](../01-tutorials/)
- **Solving a specific problem?** → See [How-To Guides](../02-how-to/)
- **Want to understand concepts?** → See [Explanation](../04-explanation/)

## Contributing

When adding reference documentation:
1. Be precise and accurate
1. Use consistent formatting
1. Include code examples where relevant
1. Keep synced with implementation
1. Cross-reference related topics

---

**Part of:** [Diátaxis Documentation Framework](https://diataxis.fr/)
