# Explanation - Understanding Dopemux

**Explanation clarifies and illuminates a particular topic.** These are understanding-oriented discussions that deepen your knowledge of how and why Dopemux works.

## Quick Navigation

- [Architecture](#architecture)
- [Concepts](#concepts)
- [Design Decisions](#design-decisions)
- [Technical Deep Dives](#technical-deep-dives)

---

## Architecture

Understand the overall system design and component interactions.

### Core Architecture
- **[Architecture Overview](architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md)** - Complete system architecture
- **[System Bible](../94-architecture/system-bible.md)** - Consolidated knowledge base
- **[Unified Architecture Guide](../94-architecture/unified-architecture-guide.md)** - Integration guide

### Component Architecture
- **[ConPort-KG 2.0 Master Plan](../94-architecture/CONPORT_KG_2.0_MASTER_PLAN.md)** - Knowledge graph architecture
- **[ConPort-KG Executive Summary](../94-architecture/CONPORT_KG_2.0_EXECUTIVE_SUMMARY.md)** - High-level overview
- **[Multi-Instance Implementation](../94-architecture/multi-instance-implementation.md)** - Multi-instance design
- **[Serena V2 Architecture](../94-architecture/serena-v2-architecture-analysis.md)** - ADHD engine architecture

### Integration Architecture
- **[Agent Integration Guide](../94-architecture/AGENT_INTEGRATION_GUIDE.md)** - Agent integration patterns
- **[Phase 2 Completion Summary](../94-architecture/PHASE_2_COMPLETION_SUMMARY.md)** - Integration milestones
- **[Integration Complete Summary](../94-architecture/INTEGRATION_COMPLETE_SUMMARY.md)** - Final integration state

---

## Concepts

Core concepts and mental models for working with Dopemux.

**Location:** `concepts/`

*To be organized from existing docs:*
- Worktree system concept
- Multi-instance concept
- ADHD optimization principles
- Session intelligence

---

## Design Decisions

Understand the reasoning behind architectural and design choices.

### Architecture Decision Records (ADRs)
Located in `../90-adr/` - Formal decision records

**Recent Key Decisions:**
- **[ADR-207: Architecture 3.0](../90-adr/ADR-207-architecture-3.0-three-layer-integration.md)** - Three-layer integration
- **[ADR-203: Task Orchestrator](../90-adr/ADR-203-task-orchestrator-un-deprecation.md)** - Orchestrator revival
- **[ADR-202: Serena V2 Validation](../90-adr/ADR-202-serena-v2-production-validation.md)** - Production readiness
- **[ADR-201: ConPort Security](../90-adr/ADR-201-conport-kg-security-hardening.md)** - Security hardening

**Location:** `design-decisions/`

*To be created: Non-ADR design rationales*

---

## Technical Deep Dives

In-depth technical explorations of specific subsystems.

### Component Deep Dives
- **[Serena V2 Technical Deep Dive](serena-v2-technical-deep-dive.md)** - ADHD engine internals
- **[ConPort Technical Deep Dive](conport-technical-deep-dive.md)** - Knowledge graph deep dive

### Integration Details
- **[Component 3: Integration Bridge](../COMPONENT_3_INTEGRATION_BRIDGE_WIRING.md)** - Bridge wiring
- **[Component 4: ConPort MCP](../COMPONENT_4_CONPORT_MCP_WIRING.md)** - MCP integration
- **[Component 5: Queries](../COMPONENT_5_CONPORT_MCP_QUERIES.md)** - Query system
- **[Component 6: Intelligence](../COMPONENT_6_ADHD_INTELLIGENCE.md)** - ADHD intelligence
- **[Component 7: Interruption Shield](../COMPONENT_7_ENVIRONMENTAL_INTERRUPTION_SHIELD.md)** - Shield design

### Performance & Analysis
- **[Component 5: Performance](../COMPONENT_5_PERFORMANCE_ANALYSIS.md)** - Performance analysis
- **[Cross-Component Analysis](../CROSS-COMPONENT-ANALYSIS.md)** - System-wide analysis

### Consolidated Documentation
- **[ADHD Complete Documentation](../ADHD_COMPLETE_DOCUMENTATION.md)** - Complete ADHD system
- **[ADHD Stack README](../ADHD_STACK_README.md)** - Stack overview
- **[Architecture Consolidation](../ARCHITECTURE-CONSOLIDATION-SYNTHESIS.md)** - Synthesis

---

## Explanation Principles

Explanations in this section:
- **Are understanding-oriented** - Deepen knowledge
- **Provide context** - Why things are as they are
- **Discuss alternatives** - Trade-offs and decisions
- **Make connections** - Between concepts and components

## Not What You're Looking For?

- **Getting started?** → See [Tutorials](../01-tutorials/)
- **Solving a problem?** → See [How-To Guides](../02-how-to/)
- **Looking up details?** → See [Reference](../03-reference/)

## Contributing

When adding explanations:
1. Focus on understanding, not instructions
2. Provide background and context
3. Discuss alternatives and trade-offs
4. Use diagrams where helpful
5. Link to related concepts

---

**Part of:** [Diátaxis Documentation Framework](https://diataxis.fr/)
