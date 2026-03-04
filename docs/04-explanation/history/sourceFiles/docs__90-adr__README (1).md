# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) that document important architectural decisions made during Dopemux development, with their context and consequences.

## 📋 What are ADRs?
Architecture Decision Records capture **architectural decisions** with their context, decision, and consequences. They help understand why certain choices were made and their long-term impact.

## 🧠 ADHD-Friendly ADR Format
Our ADRs follow a streamlined format optimized for neurodivergent developers:

```markdown
# ADR-XXX: [Title]

**Status**: [Proposed | Accepted | Deprecated | Superseded]
**Date**: YYYY-MM-DD
**Deciders**: @username, @username
**Tags**: #category #impact-level

## 🎯 Context
What situation led to this decision?

## 🎪 Decision
What decision was made?

## 🔄 Consequences
### Positive
- ✅ Benefit 1
- ✅ Benefit 2

### Negative
- ❌ Tradeoff 1
- ❌ Tradeoff 2

### Neutral
- ℹ️ Consideration 1
- ℹ️ Consideration 2

## 🔗 References
- Links to related documents
- External research
```

## 📂 ADR Categories

### Core Architecture (001-099)
- [ADR-001: Hub-and-Spoke Architecture](001-hub-spoke-architecture.md)
- [ADR-002: MCP Protocol Selection](002-mcp-protocol-selection.md)
- [ADR-003: SQLite for Context Storage](003-sqlite-context-storage.md)
- [ADR-004: Python as Primary Language](004-python-primary-language.md)

### ADHD Optimizations (100-199)
- [ADR-101: 25-Minute Task Chunks](101-task-chunk-duration.md)
- [ADR-102: Auto-Save Interval](102-auto-save-interval.md)
- [ADR-103: Attention State Classification](103-attention-classification.md)
- [ADR-104: Gentle Error Handling](104-gentle-error-handling.md)
- [ADR-105: Progressive Disclosure Pattern](105-progressive-disclosure.md)

### Integration Decisions (200-299)
- [ADR-201: Claude Code Integration Strategy](201-claude-code-integration.md)
- [ADR-202: Leantime as Project Management Tool](202-leantime-selection.md)
- [ADR-203: Docker for MCP Server Deployment](203-docker-mcp-deployment.md)
- [ADR-204: Task-Master AI Integration](204-task-master-integration.md)

### Development Workflow (300-399)
- [ADR-301: Testing Strategy](301-testing-strategy.md)
- [ADR-302: Configuration Management](302-configuration-management.md)
- [ADR-303: CLI Interface Design](303-cli-interface-design.md)
- [ADR-304: Error Logging Approach](304-error-logging.md)

### User Experience (400-499)
- [ADR-401: Visual Complexity Levels](401-visual-complexity.md)
- [ADR-402: Notification System Design](402-notification-system.md)
- [ADR-403: Help System Integration](403-help-system.md)
- [ADR-404: Accessibility Requirements](404-accessibility-requirements.md)

### Data & Security (500-599)
- [ADR-501: Context Data Privacy](501-context-privacy.md)
- [ADR-502: Session Backup Strategy](502-session-backup.md)
- [ADR-503: API Key Management](503-api-key-management.md)
- [ADR-504: Health Data Collection](504-health-data-collection.md)

### Performance & Scalability (600-699)
- [ADR-601: Context Restoration Performance](601-context-restoration-performance.md)
- [ADR-602: Memory Usage Optimization](602-memory-optimization.md)
- [ADR-603: Concurrent MCP Server Management](603-concurrent-mcp-management.md)
- [ADR-604: Database Performance Tuning](604-database-performance.md)

## 🔄 ADR Lifecycle

### Status Definitions
- **🟡 Proposed**: Under consideration, seeking feedback
- **🟢 Accepted**: Approved and implemented
- **🔴 Deprecated**: No longer recommended, but still in use
- **⚪ Superseded**: Replaced by a newer ADR

### Review Process
1. **Draft**: Create ADR with "Proposed" status
2. **Review**: Team/community feedback period
3. **Decision**: Accept, reject, or request changes
4. **Implementation**: Update status to "Accepted" when implemented
5. **Evolution**: Update status if superseded or deprecated

## 🏷️ ADR Tags

### Impact Level
- `#critical` - Core architectural decisions
- `#major` - Significant feature decisions
- `#minor` - Implementation detail decisions

### Category Tags
- `#adhd` - ADHD optimization decisions
- `#integration` - External service integration
- `#performance` - Speed and efficiency
- `#security` - Safety and privacy
- `#ux` - User experience
- `#development` - Development workflow

### Component Tags
- `#cli` - Command-line interface
- `#context` - Context management
- `#health` - Health monitoring
- `#mcp` - MCP server related
- `#tasks` - Task management

## 🔍 Finding ADRs

### By Status
```bash
# Find all accepted ADRs
grep -r "Status.*Accepted" docs/90-adr/

# Find proposed ADRs needing review
grep -r "Status.*Proposed" docs/90-adr/
```

### By Category
- **ADHD Features**: ADR-100 series
- **Integrations**: ADR-200 series
- **Development**: ADR-300 series
- **User Experience**: ADR-400 series

### By Impact
- **Critical Decisions**: Search for `#critical` tag
- **Recent Changes**: Sort by date in filename/header

## 🧭 Related Documentation
- **[Explanations](../04-explanation/)** - Understanding why decisions were made
- **[Architecture](../94-architecture/)** - System design documentation
- **[RFCs](../91-rfc/)** - Proposed changes and features
- **[Runbooks](../92-runbooks/)** - Operational procedures

## 📝 Contributing ADRs
1. Use the next available number in appropriate range
2. Follow the ADHD-friendly format above
3. Include relevant tags and references
4. Start with "Proposed" status
5. Link to related explanations and documentation

---
*ADRs help maintain institutional knowledge and provide context for future decisions in an ADHD-friendly format.*