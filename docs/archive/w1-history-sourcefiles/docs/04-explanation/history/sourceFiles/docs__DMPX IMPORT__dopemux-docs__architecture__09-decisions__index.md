# Architecture Decision Records (ADRs)

This directory contains all architectural decisions made for the Dopemux platform, organized chronologically with proper numbering.

## ADR Index

### Core Architecture Decisions

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| [ADR-001](./ADR-001-architecture-paradigm.md) | Hub-and-Spoke Architecture with Agent Orchestration | ✅ Accepted | 2025-09-17 | High |
| [ADR-002](./ADR-002-adhd-accommodation-integration.md) | ADHD Accommodation Integration Strategy | ✅ Accepted | 2025-09-17 | High |
| [ADR-003](./ADR-003-editor-implementation.md) | Integrated Code Editor Implementation Strategy | ✅ Accepted | 2025-09-17 | High |
| [ADR-004](./ADR-004-visual-workflow-ui.md) | Visual Workflow UI in Terminal Environment | ✅ Accepted | 2025-09-17 | High |

### Technical Implementation Decisions

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| ADR-005 | AI Integration Patterns | 🔄 Draft | 2025-09-17 | High |
| ADR-006 | Memory Architecture (Letta vs ConPort) | 🔄 Draft | 2025-09-17 | High |
| ADR-007 | MCP Server Selection & Priority | 🔄 Draft | 2025-09-17 | Medium |
| ADR-008 | Task Management Integration | 🔄 Draft | 2025-09-17 | Medium |
| ADR-009 | Routing Logic Architecture | 🔄 Draft | 2025-09-17 | Medium |
| ADR-010 | Session Management Strategy | 🔄 Draft | 2025-09-17 | Medium |

### Infrastructure & Operations

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| ADR-011 | Local-First Data Architecture | ✅ Accepted | 2025-09-17 | Medium |
| ADR-012 | Embeddings Provider Selection | ✅ Accepted | 2025-09-17 | Low |
| ADR-013 | Data Classification Schema | ✅ Accepted | 2025-09-17 | Medium |
| ADR-014 | Ownership Policy Framework | ✅ Accepted | 2025-09-17 | Medium |
| ADR-015 | Correctness SLI Definition | ✅ Accepted | 2025-09-17 | Medium |

### Platform & Security

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| ADR-016 | Connector Priority Framework | ✅ Accepted | 2025-09-17 | Low |
| ADR-017 | Connector Auth Model | ✅ Accepted | 2025-09-17 | Medium |
| ADR-018 | Chunking Defaults Strategy | ✅ Accepted | 2025-09-17 | Low |
| ADR-019 | Provenance Schema Design | ✅ Accepted | 2025-09-17 | Medium |

## ADR Categories

### By Impact Level
- **High Impact**: Fundamental architecture and user experience decisions
- **Medium Impact**: Implementation choices affecting multiple components
- **Low Impact**: Technical details and operational configurations

### By Status
- **✅ Accepted**: Approved and implementation ready
- **🔄 Draft**: Under development, extracted from research
- **🤔 Proposed**: Submitted for review
- **❌ Rejected**: Decided against with rationale
- **🔄 Superseded**: Replaced by newer decision

## Decision Process

### Creating ADRs
1. **Template**: Use the standard ADR template
2. **Numbering**: Sequential numbering (ADR-XXX)
3. **Review**: Architecture team approval required
4. **Implementation**: Link to implementation progress

### ADR Template
```markdown
# ADR-XXX: [Title]

**Status**: [Proposed|Accepted|Rejected|Superseded]
**Date**: YYYY-MM-DD
**Deciders**: [List of decision makers]
**Technical Story**: [Brief context]

## Context
[Problem and constraints]

## Decision
[What we decided]

## Rationale
[Why we decided this way]

## Alternatives Considered
[Other options and why rejected]

## Consequences
[Positive and negative impacts]
```

## Recent Decisions

### September 2025
- **ADR-001**: Established hub-and-spoke architecture paradigm
- **ADR-002**: Defined comprehensive ADHD accommodation strategy
- **ADR-003**: Selected Helix editor fork for integrated development
- **ADR-004**: Chose ASCII art approach for terminal-native workflow visualization

## Outstanding Decisions

### High Priority
1. **Memory Architecture**: Final decision between Letta and ConPort
2. **AI Integration**: Standardize patterns across all AI interactions
3. **MCP Server Priority**: Define mandatory vs optional servers
4. **Task Management**: Clarify Leantime vs Task-Master roles

### Medium Priority
1. **Routing Logic**: Finalize multi-model orchestration approach
2. **Session Management**: Define persistence and recovery strategies
3. **Performance Targets**: Establish quantitative SLAs
4. **Security Model**: Define authentication and authorization

## Cross-References

### Related Documentation
- [System Architecture](../05-building-blocks/)
- [Quality Requirements](../10-quality/)
- [Risk Register](../11-risks/)

### Implementation Status
- See [Implementation Guides](../../implementation/)
- Track progress in [Project Roadmap](../../product/roadmap.md)

---

**Last Updated**: 2025-09-17
**Next Review**: 2025-10-17 (Monthly ADR Review)