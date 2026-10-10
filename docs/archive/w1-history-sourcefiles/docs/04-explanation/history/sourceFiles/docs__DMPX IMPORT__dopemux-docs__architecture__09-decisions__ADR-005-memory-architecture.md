# ADR-005: Memory Architecture - Letta Framework Selection

**Status**: Accepted
**Date**: 2025-09-17
**Deciders**: Architecture Team, Memory Research Group
**Technical Story**: Selection of memory persistence and context management system for Dopemux

## Context

Dopemux requires sophisticated memory management to support:

1. **Session Persistence**: Maintain context across terminal sessions and restarts
2. **Cross-Session Learning**: Accumulate knowledge about user patterns and preferences
3. **Project Context**: Preserve project-specific decisions, patterns, and history
4. **ADHD Accommodation**: Reduce cognitive load through automatic context restoration
5. **Unlimited Context**: Support large-scale context preservation beyond token limits

Three primary options were evaluated: Letta Framework, ConPort, and custom SQLite solution.

## Decision

We will use **Letta Framework** as the primary memory system for Dopemux.

### Implementation Strategy:

```yaml
memory_architecture:
  primary: "Letta Framework (cloud or self-hosted)"
  fallback: "SQLite + local indexing"
  integration: "MCP client for Letta API"

memory_types:
  session_memory:
    provider: "Letta memory blocks"
    retention: "90 days active, archived thereafter"

  project_memory:
    provider: "Letta + local SQLite"
    retention: "Permanent with project lifecycle"

  user_patterns:
    provider: "Letta archival store"
    retention: "Permanent with privacy controls"
```

### Memory Block Structure:

```rust
enum MemoryBlockType {
    Persona,           // User working style and preferences
    ProjectContext,    // Project-specific patterns and decisions
    Decisions,         // Architecture and implementation choices
    Patterns,          // Recurring code and workflow patterns
    Runbook,          // Process documentation and procedures
    Lessons,          // Learned insights and improvements
}

struct MemoryBlock {
    block_type: MemoryBlockType,
    content: String,
    metadata: BlockMetadata,
    embeddings: Vec<f32>,
    last_updated: DateTime<Utc>,
}

struct BlockMetadata {
    project_id: Option<String>,
    user_id: String,
    tags: Vec<String>,
    importance: ImportanceLevel,
    access_count: u32,
}
```

## Rationale

### Advantages of Letta Framework:

1. **Advanced Memory Capabilities**:
   - Self-editing memory blocks with intelligent updates
   - 74.0% LoCoMo benchmark accuracy for memory operations
   - Unlimited context through archival vector store
   - Automatic memory consolidation and organization

2. **Enterprise-Ready**:
   - Hosted service option ($39/month Plus tier)
   - Self-hosted deployment available
   - Comprehensive API and MCP integration
   - Production-grade reliability and scaling

3. **ADHD-Friendly Features**:
   - Automatic context restoration reduces cognitive load
   - Pattern recognition helps with routine tasks
   - Personalized accommodation learning
   - Seamless background operation

4. **Developer Productivity**:
   - No need to build custom memory systems
   - Rich API for integration
   - Active development and community
   - Proven performance in similar applications

### Trade-offs Accepted:

1. **External Dependency**:
   - Relies on Letta service availability
   - **Mitigation**: Local SQLite fallback, self-hosted option

2. **Cost Considerations**:
   - $39/month for hosted service
   - **Mitigation**: Enterprise pricing scales, self-hosted alternative

3. **Data Privacy**:
   - External service handles sensitive development data
   - **Mitigation**: Encryption in transit/at rest, self-hosted deployment

## Alternatives Considered

### ConPort (Custom Solution) - Rejected
- **Pros**: Full control, no external dependencies, cost-effective
- **Cons**: Significant development effort, limited memory sophistication, maintenance burden
- **Verdict**: Resource allocation inefficient vs. proven solution

### SQLite + Custom Memory - Rejected
- **Pros**: Simple, local-only, no external dependencies
- **Cons**: Limited context size, no intelligent consolidation, manual memory management
- **Verdict**: Insufficient for sophisticated memory requirements

### OpenMemory Framework - Considered but Rejected
- **Pros**: Open source, customizable
- **Cons**: Early stage, limited features vs. Letta, uncertain maintenance
- **Verdict**: Too immature for production deployment

## Implementation Strategy

### Phase 1: Basic Integration (Weeks 1-2)
- Letta MCP client implementation
- Basic memory block operations (read/write)
- Session persistence for active projects
- Fallback SQLite implementation

### Phase 2: Advanced Memory Features (Weeks 3-4)
- Self-editing memory blocks
- Automatic context consolidation
- Pattern recognition and learning
- Cross-session knowledge transfer

### Phase 3: ADHD Optimizations (Weeks 5-6)
- Cognitive load reduction features
- Intelligent context suggestions
- Attention pattern learning
- Personalized accommodation adaptation

### Phase 4: Enterprise Features (Weeks 7-8)
- Multi-tenant memory isolation
- Advanced privacy controls
- Backup and recovery systems
- Performance optimization

## Memory Lifecycle Management

### Data Retention Policies

```yaml
retention_policies:
  session_data:
    active_retention: "90 days"
    archive_retention: "1 year"
    cleanup_policy: "automatic"

  project_data:
    active_retention: "project_lifetime"
    archive_retention: "permanent"
    cleanup_policy: "manual"

  personal_patterns:
    active_retention: "permanent"
    archive_retention: "permanent"
    cleanup_policy: "user_controlled"
```

### Privacy and Security

```rust
struct PrivacyControls {
    data_residency: DataResidency,
    encryption: EncryptionConfig,
    access_controls: AccessControlList,
    audit_logging: AuditConfig,
}

enum DataResidency {
    Cloud,              // Letta hosted service
    SelfHosted,         // User-controlled Letta instance
    LocalOnly,          // SQLite fallback only
    Hybrid,             // Mix based on sensitivity
}
```

## Success Metrics

### Performance Targets:
- **Context Retrieval**: <500ms for relevant memory blocks
- **Memory Consolidation**: Background processing, no user wait
- **Session Restoration**: <2s full context recovery
- **Memory Accuracy**: >90% relevant context suggestions

### User Experience:
- **Context Continuity**: Seamless session transitions
- **Learning Effectiveness**: Improved assistance over time
- **Cognitive Load**: Reduced mental overhead for context management
- **Privacy Confidence**: Clear data handling and control

## Risks and Mitigations

### High Risk: Service Availability
- **Risk**: Letta service outages disrupt memory operations
- **Probability**: Low (enterprise SLA)
- **Impact**: Medium (fallback to local)
- **Mitigation**:
  - SQLite fallback for critical operations
  - Self-hosted deployment option
  - Local caching of recent memory blocks

### Medium Risk: Data Migration Complexity
- **Risk**: Difficulty migrating from local to Letta or between instances
- **Probability**: Medium
- **Impact**: Medium (data accessibility)
- **Mitigation**:
  - Standardized export/import formats
  - Migration tooling development
  - Gradual migration capabilities

### Low Risk: Cost Escalation
- **Risk**: Memory usage exceeds plan limits
- **Probability**: Low
- **Impact**: Low (predictable pricing)
- **Mitigation**:
  - Usage monitoring and alerts
  - Intelligent memory pruning
  - Multiple pricing tier options

## Validation Approach

### Technical Validation:
1. **Performance Testing**: Memory retrieval and consolidation speed
2. **Reliability Testing**: Service availability and failover scenarios
3. **Integration Testing**: MCP client functionality and error handling
4. **Scale Testing**: Large project and multi-user scenarios

### User Validation:
1. **ADHD Developer Testing**: Cognitive load reduction measurement
2. **Context Continuity**: Session restoration effectiveness
3. **Learning Assessment**: Memory system improvement over time
4. **Privacy Validation**: User comfort with data handling

## Consequences

### Positive Consequences:
- **Advanced Memory Capabilities**: Self-editing blocks and unlimited context
- **Reduced Development Effort**: Proven solution vs. custom development
- **ADHD Accommodation**: Automatic context management reduces cognitive load
- **Enterprise Scalability**: Production-ready system with hosting options

### Negative Consequences:
- **External Dependency**: Reliance on Letta service and API
- **Cost Structure**: Monthly service fees vs. one-time development
- **Data Privacy Considerations**: External service handling sensitive data
- **Migration Complexity**: Potential difficulty moving between systems

### Monitoring and Review:
- **Performance Monitoring**: Memory operation latency and success rates
- **Cost Tracking**: Monthly usage and pricing optimization
- **User Feedback**: Memory effectiveness and cognitive load impact
- **Technology Assessment**: Annual review of memory system alternatives

---

**ADR Status**: Accepted and Implementation Ready
**Review Date**: 2025-12-17 (Quarterly Review)
**Implementation Priority**: High - Core Platform Capability