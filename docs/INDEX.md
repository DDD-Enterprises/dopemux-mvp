# Dopemux Documentation Index

**Last Updated**: 2025-10-05
**Framework**: Diátaxis (Learn, Do, Understand, Reference)
**Organization**: ADHD-optimized progressive disclosure

---

## 📚 Documentation Structure

This project follows the **Diátaxis documentation framework** for systematic organization:

```
docs/
├── 01-tutorial/        # Learning-oriented (step-by-step lessons)
├── 02-how-to/          # Task-oriented (practical guides)
├── 03-reference/       # Information-oriented (technical specifications)
├── 04-explanation/     # Understanding-oriented (conceptual deep dives)
├── 90-adr/             # Architecture Decision Records
├── 91-rfc/             # Request for Comments (proposals)
└── 94-architecture/    # System architecture documentation
```

---

## 🎓 01-tutorial/ - Learn by Doing

*Step-by-step tutorials for getting started*

[Currently empty - tutorials coming soon]

**Planned**:
- Getting Started with Dopemux
- Your First ADHD-Optimized Session
- Understanding the Two-Plane Architecture

---

## 🔧 02-how-to/ - Practical Guides

*Task-oriented guides for specific operations*

### Core Workflows
- **[multi-instance-workflow.md](02-how-to/multi-instance-workflow.md)** - Managing multiple concurrent work streams
- **[instance-slash-commands.md](02-how-to/instance-slash-commands.md)** - Using instance-specific commands
- **[instance-state-persistence.md](02-how-to/instance-state-persistence.md)** - Persisting and restoring instance state

### System Setup & Configuration
- **[serena-v2-deployment.md](02-how-to/serena-v2-deployment.md)** - Deploying Serena LSP server
- **[serena-v2-production-deployment.md](02-how-to/serena-v2-production-deployment.md)** - Production deployment guide
- **[metamcp-setup.md](02-how-to/metamcp-setup.md)** - Setting up MetaMCP orchestration
- **[metamcp-quickstart.md](02-how-to/metamcp-quickstart.md)** - Quick start guide for MetaMCP
- **[metamcp-debugging.md](02-how-to/metamcp-debugging.md)** - Debugging MetaMCP issues
- **[role-switching-quickstart.md](02-how-to/role-switching-quickstart.md)** - Switching between PLAN/ACT modes

---

## 📖 03-reference/ - Technical Specifications

*Information-oriented technical references*

### MCP Server References
- **[serena-v2-mcp-tools.md](serena-v2-mcp-tools.md)** - Complete Serena MCP tools documentation

### Configuration & Checklists
- **[metamcp-configuration-checklist.md](03-reference/metamcp-configuration-checklist.md)** - Configuration validation checklist
- **[metamcp-post-restart-config.md](03-reference/metamcp-post-restart-config.md)** - Post-restart configuration steps
- **[metamcp-tool-mapping.md](03-reference/metamcp-tool-mapping.md)** - Tool routing and mapping reference

### Test & Validation Reports
- **[serena-v2-validation-report.md](03-reference/serena-v2-validation-report.md)** - Serena v2 validation results
- **[serena-v2-test-summary.md](03-reference/serena-v2-test-summary.md)** - Test coverage and results

### Feature Documentation
- **[F001-untracked-work-detection.md](03-reference/F001-untracked-work-detection.md)** - Untracked work detection feature
- **[F002-multi-session-support.md](03-reference/F002-multi-session-support.md)** - Multi-session support specification

---

## 💡 04-explanation/ - Understanding Concepts

*Conceptual explanations and deep technical dives*

### Technical Deep Dives
- **[serena-v2-technical-deep-dive.md](04-explanation/serena-v2-technical-deep-dive.md)** - Serena v2 architecture and design
- **[conport-technical-deep-dive.md](04-explanation/conport-technical-deep-dive.md)** - ConPort knowledge graph deep dive

### Architecture Explanations
- **[architecture/](04-explanation/architecture/)** - Architectural concept explanations

### Backlogs & Planning
- **[backlog/](04-explanation/backlog/)** - Feature backlogs and planning docs

---

## 🏗️ 94-architecture/ - System Architecture

*High-level system design and architectural documentation*

### Core Architecture Docs
- **[system-bible.md](94-architecture/system-bible.md)** - Complete system architecture reference
- **[unified-architecture-guide.md](94-architecture/unified-architecture-guide.md)** - Unified two-plane architecture
- **[conport-kg-project-summary.md](94-architecture/conport-kg-project-summary.md)** - ConPort knowledge graph project overview
- **[multi-instance-implementation.md](94-architecture/multi-instance-implementation.md)** - Multi-instance architecture
- **[serena-v2-architecture-analysis.md](94-architecture/serena-v2-architecture-analysis.md)** - Serena v2 architectural analysis

---

## 📝 90-adr/ - Architecture Decision Records

*Record of architectural decisions and their rationale*

### ADRs
- **[ADR-180-automatic-instance-resume.md](90-adr/ADR-180-automatic-instance-resume.md)** - Automatic instance resumption
- **[ADR-197-task-epic-workflow-system.md](90-adr/ADR-197-task-epic-workflow-system.md)** - Task-Epic workflow system

*See [90-adr/](90-adr/) for complete list*

---

## 🚀 91-rfc/ - Request for Comments

*Proposals and design documents for review*

[See 91-rfc/ directory for proposals]

---

## 🔍 Quick Navigation

### By Topic

**ADHD Accommodations**:
- Multi-instance workflow → [02-how-to/multi-instance-workflow.md](02-how-to/multi-instance-workflow.md)
- Session persistence → [02-how-to/instance-state-persistence.md](02-how-to/instance-state-persistence.md)

**Code Intelligence**:
- Serena deployment → [02-how-to/serena-v2-deployment.md](02-how-to/serena-v2-deployment.md)
- Serena deep dive → [04-explanation/serena-v2-technical-deep-dive.md](04-explanation/serena-v2-technical-deep-dive.md)
- Serena tools reference → [serena-v2-mcp-tools.md](serena-v2-mcp-tools.md)

**Knowledge Management**:
- ConPort deep dive → [04-explanation/conport-technical-deep-dive.md](04-explanation/conport-technical-deep-dive.md)
- ConPort architecture → [94-architecture/conport-kg-project-summary.md](94-architecture/conport-kg-project-summary.md)

**System Architecture**:
- System bible → [94-architecture/system-bible.md](94-architecture/system-bible.md)
- Unified architecture → [94-architecture/unified-architecture-guide.md](94-architecture/unified-architecture-guide.md)

**MCP Integration**:
- MetaMCP setup → [02-how-to/metamcp-setup.md](02-how-to/metamcp-setup.md)
- MetaMCP debugging → [02-how-to/metamcp-debugging.md](02-how-to/metamcp-debugging.md)
- MetaMCP configuration → [03-reference/metamcp-configuration-checklist.md](03-reference/metamcp-configuration-checklist.md)

---

## 📊 Documentation Statistics

- **Total Documentation Files**: ~40 markdown files
- **Tutorials**: 0 (coming soon)
- **How-To Guides**: 9 guides
- **Reference Docs**: 8 specifications
- **Explanations**: 3 deep dives
- **Architecture Docs**: 5 architectural documents
- **ADRs**: 2+ decision records
- **RFCs**: Active proposals in 91-rfc/

---

## 🎯 Contributing to Documentation

When adding documentation:

1. **Choose the right category**:
   - Learning? → `01-tutorial/`
   - Solving a problem? → `02-how-to/`
   - Technical specs? → `03-reference/`
   - Explaining concepts? → `04-explanation/`
   - Architecture decisions? → `90-adr/`
   - Proposals? → `91-rfc/`

2. **Use descriptive filenames**: `kebab-case-with-clear-purpose.md`

3. **Update this INDEX.md** when adding new docs

4. **Follow ADHD principles**:
   - Progressive disclosure (summary → details)
   - Clear section headers
   - Actionable next steps
   - Visual indicators (emoji, formatting)

---

**Need help?** See the main [README.md](../README.md) or check [.claude/CLAUDE.md](../.claude/CLAUDE.md) for project-specific guidance.
