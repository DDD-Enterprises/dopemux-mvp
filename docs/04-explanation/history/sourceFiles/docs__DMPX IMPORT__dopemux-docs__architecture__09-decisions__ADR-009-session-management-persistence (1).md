# ADR-009: Session Management and Persistence Strategy

## Status
**Accepted** - Multi-tiered memory architecture with Letta Framework and Redis

## Context

Dopemux requires sophisticated session management and persistence to support:
- ADHD accommodation through seamless context restoration
- Multi-agent collaboration with shared memory
- Cross-session learning and knowledge retention
- Real-time synchronization across multiple interfaces
- Large context management with token efficiency

The system must handle both structured data (tasks, projects) and unstructured context (conversations, decisions, mental models) while maintaining performance under ADHD-critical latency requirements (<50ms for attention-critical operations).

## Decision

**Multi-Tiered Memory Architecture** combining Letta Framework for hierarchical memory management with Redis for high-performance caching and PostgreSQL for long-term storage.

## Architecture Overview

### Three-Tier Memory System
```yaml
Memory_Architecture:
  Hot_Memory:    # In-memory, immediate access
    storage: In-process cache + Redis
    latency: < 10ms
    retention: Current session + recent interactions
    use_cases: [active_context, user_state, current_tasks]

  Warm_Memory:   # Frequently accessed historical data
    storage: Redis cluster + Letta Framework
    latency: < 100ms
    retention: Days to weeks
    use_cases: [recent_sessions, project_context, user_patterns]

  Cold_Memory:   # Long-term storage and knowledge
    storage: PostgreSQL + Letta external storage
    latency: < 500ms
    retention: Months to years
    use_cases: [project_history, learned_patterns, user_preferences]
```

### Letta Framework Integration
```yaml
letta_architecture:
  in_context_memory:
    type: Editable blocks within LLM context
    capacity: ~8K tokens (configurable)
    access: Direct manipulation via tool calls
    use_cases: [current_conversation, active_decisions]

  memory_blocks:
    type: Discrete, labeled units with API access
    capacity: Unlimited (external storage)
    access: Archival/recall through semantic search
    use_cases: [project_knowledge, user_preferences, learned_patterns]

  out_of_context_memory:
    type: External archival storage
    capacity: Gigabyte-scale document corpus
    access: Hierarchical retrieval with embeddings
    use_cases: [documentation, code_history, research_artifacts]
```

## Technical Implementation

### Memory Transition Strategies
```yaml
promotion_algorithms:
  importance_scoring:
    threshold: 0.8 (promotes to next tier)
    factors: [access_frequency, user_explicit_save, decision_impact]
    decay: Time-based and frequency-based degradation

  consolidation_patterns:
    background_tasks: Scheduled memory consolidation
    event_driven: Triggered by session end or major decisions
    cognitive_promotion: AI-determined importance elevation

conflict_resolution:
  temporal_metadata: Version tracking with timestamps
  multi_layer_search: Fallback strategies across tiers
  consistency_validation: Cross-tier integrity checks
```

### Database Architecture
```yaml
polyglot_persistence:
  redis_cluster:
    purpose: High-performance caching and real-time data
    performance: 62% higher throughput, sub-100ms latency
    use_cases: [session_state, user_preferences, hot_cache]
    configuration:
      - cluster_mode: enabled
      - persistence: RDB + AOF
      - memory_policy: allkeys-lru

  postgresql_primary:
    purpose: Structured data and complex queries
    performance: Order-of-magnitude throughput with pgvector
    use_cases: [projects, tasks, user_data, audit_logs]
    extensions: [pgvector, pg_stat_statements, pg_cron]

  letta_storage:
    purpose: Hierarchical memory and semantic search
    performance: 74% accuracy on LoCoMo benchmarks
    use_cases: [context_memory, knowledge_graphs, agent_collaboration]
```

### Context Compression and Management
```yaml
compression_techniques:
  token_reduction: 40-60% through progressive summarization
  attention_focused_pruning: Remove low-weight tokens
  structural_compression: Maintain phrasing while reducing redundancy
  semantic_compression: Embeddings-based information density

large_context_handling:
  dynamic_loading: Just-in-time relevant section injection
  token_budget_management: (input + output) ≤ context_window - 20%
  thinking_tokens: 16k+ optimal for complex tasks
  repository_aware_chunking: Semantic boundaries over arbitrary limits
```

## Session Lifecycle Management

### Session Initialization
```yaml
session_start:
  1. Load user profile and preferences from cold storage
  2. Restore recent context from warm memory (Redis)
  3. Initialize Letta memory blocks with project context
  4. Establish WebSocket connections for real-time updates
  5. Activate ADHD accommodation settings

context_restoration:
  hot_memory: Immediate access to last session state
  warm_memory: Recent project context and decisions
  cold_memory: Historical patterns and learned preferences
  letta_blocks: Semantic context reconstruction
```

### Real-Time Synchronization
```yaml
update_propagation:
  websocket_streaming: Persistent connections for live updates
  event_sourcing: Immutable event log for reconstruction
  cqrs_pattern: Separate read/write models for performance

state_preservation:
  checkpoint_triggers:
    - periodic: Every 30 minutes
    - event_based: Major decisions or context switches
    - user_initiated: Explicit save commands
    - session_end: Automatic persistence

  immutable_capture:
    - event_sourcing: Complete audit trail
    - snapshot_delta: Periodic full state + incremental changes
    - copy_on_write: Efficient state branching
```

### Cross-Agent Context Propagation
```yaml
memory_sharing_protocols:
  centralized_blackboard: Common memory space for all agents
  distributed_vector_stores: Semantic similarity search
  knowledge_graphs: Semantic relationship modeling

mcp_integration:
  resource_primitives: Point-to-point memory sharing
  structured_handoff: Context inheritance protocols
  contextual_annotations: Agent interpretation layering

context_inheritance:
  hierarchical_flows: Organization → Team → Project → Task
  role_based_propagation: Agent responsibility matching
  selective_sharing: Permission and relevance filtering
```

## ADHD-Specific Optimizations

### Attention Management
```yaml
context_preservation:
  seamless_restoration: Zero cognitive overhead on return
  decision_history: Track and restore mental models
  progress_continuity: Visual progress state maintenance
  interruption_recovery: Graceful handling of context switches

cognitive_load_reduction:
  automatic_summarization: Reduce information overload
  priority_highlighting: Focus attention on critical items
  distraction_filtering: Hide non-essential context
  break_point_preservation: Save state at natural boundaries
```

### Executive Function Support
```yaml
automated_organization:
  context_categorization: Automatic tagging and grouping
  deadline_tracking: Temporal context awareness
  dependency_visualization: Relationship mapping
  energy_pattern_recognition: Optimal work time identification

memory_augmentation:
  external_memory: Reliable storage for unreliable memory
  pattern_recognition: Learn user habits and preferences
  decision_support: Historical context for similar situations
  reminder_systems: Proactive notification of important items
```

## Performance Characteristics

### Latency Targets
```yaml
adhd_critical_operations:
  context_switch: < 50ms
  session_restore: < 500ms
  memory_recall: < 200ms
  state_save: < 100ms

system_performance:
  redis_operations: < 10ms p99
  postgresql_queries: < 100ms p95
  letta_semantic_search: < 500ms
  full_session_restore: < 2s
```

### Scalability Metrics
```yaml
concurrent_users:
  target: 1000+ simultaneous sessions
  memory_per_session: 10-50MB
  redis_throughput: 100K+ ops/sec
  postgresql_connections: 200+ concurrent

storage_efficiency:
  compression_ratio: 40-60% reduction
  deduplication: Cross-user pattern sharing
  archival_policy: Automated cold storage migration
  cleanup_automation: Expired session removal
```

## Data Privacy and Security

### Data Protection
```yaml
encryption:
  at_rest: AES-256 for all persistent storage
  in_transit: TLS 1.3 for all communications
  in_memory: Memory protection for sensitive data

access_control:
  user_isolation: Strict session and memory separation
  role_based_access: Fine-grained permission system
  audit_logging: Complete access trail
  data_residency: Configurable geographic constraints
```

### GDPR Compliance
```yaml
privacy_by_design:
  data_minimization: Collect only necessary context
  purpose_limitation: Use data only for intended purposes
  storage_limitation: Automated retention policies
  user_control: Granular privacy controls

right_to_erasure:
  complete_deletion: All tiers and backups
  anonymization: Remove personal identifiers
  downstream_propagation: Notify dependent systems
  verification: Audit trails for deletion confirmation
```

## Monitoring and Observability

### Performance Monitoring
```yaml
key_metrics:
  - session_restore_latency
  - memory_hit_ratios
  - context_compression_efficiency
  - user_satisfaction_scores

alerting_thresholds:
  - p95_latency > 2x target
  - memory_hit_ratio < 85%
  - error_rate > 1%
  - session_loss_rate > 0.1%
```

### Health Checks
```yaml
system_health:
  redis_cluster: Connection pool and memory usage
  postgresql: Query performance and connection count
  letta_framework: Semantic search accuracy and latency
  mcp_connections: Server availability and response times

automated_recovery:
  circuit_breakers: Prevent cascade failures
  graceful_degradation: Fallback to cached data
  self_healing: Automatic restart of failed components
  rollback_capabilities: Revert to last known good state
```

## Consequences

### Positive
- **Seamless Context Restoration**: ADHD users never lose work state
- **Intelligent Memory Management**: AI-powered importance and retention
- **Cross-Session Learning**: System improves through usage patterns
- **High Performance**: Sub-50ms response for attention-critical operations
- **Scalable Architecture**: Multi-tier design supports growth

### Negative
- **System Complexity**: Multiple storage systems require coordination
- **Resource Usage**: Memory and storage overhead for comprehensive persistence
- **Privacy Concerns**: Extensive data collection requires careful handling
- **Backup Complexity**: Multi-tier backup and recovery procedures

### Risks and Mitigations
- **Data Loss**: Event sourcing and multi-tier backups
- **Performance Degradation**: Caching strategies and horizontal scaling
- **Privacy Breaches**: Encryption, access controls, and audit logging
- **Vendor Lock-in**: Open source components and standard protocols

## Related Decisions
- **ADR-005**: Letta Framework provides memory architecture foundation
- **ADR-008**: Task management integration leverages session persistence
- **ADR-006**: MCP servers coordinate through shared memory context
- **Future ADR-010**: Custom agent R&D builds on persistent memory

## References
- Context Management Research: `/research/findings/context-management-frameworks.md`
- Redis Caching Strategy: `/research/findings/context-management-redis-caching.md`
- Letta Framework Guide: `/research/architecture/Letta Memory Framework- Comprehensive Technical Guide.md`
- MCP Protocol: [Model Context Protocol](https://modelcontextprotocol.io/)