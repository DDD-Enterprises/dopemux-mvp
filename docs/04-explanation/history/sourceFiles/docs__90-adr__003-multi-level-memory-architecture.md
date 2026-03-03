# ADR-003: Multi-Level Memory Architecture

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX memory architecture team
**Tags**: #critical #memory #architecture #databases

## 🎯 Context

DOPEMUX requires sophisticated memory management across multiple dimensions: individual agents, sessions, projects, personal data, and global knowledge. A single database approach cannot efficiently handle the diverse access patterns and storage requirements.

### Memory Requirements Analysis
- **Agent Memory**: Conversation history, specialization knowledge, learned patterns
- **Session Memory**: Current context, decisions, multi-agent coordination
- **Project Memory**: Long-term codebase knowledge, architectural decisions
- **Personal Memory**: ADHD accommodations, preferences, cross-session learning
- **Global Memory**: Universal patterns, framework knowledge, best practices
- **Data Lakes**: Personal productivity data, communication archives

### Access Pattern Diversity
- **Real-time queries**: Sub-100ms for context switching (ADHD requirement)
- **Semantic search**: Vector similarity for code and documentation
- **Relational queries**: Structured data with complex joins
- **Graph traversal**: Dependency tracking and relationship analysis
- **Cache access**: Immediate retrieval for active session state
- **Analytical queries**: Pattern analysis across large datasets

### Single Database Limitations
- SQLite: Limited concurrency, no vector search
- PostgreSQL: Slower for high-frequency updates, no native vector ops
- Vector DB only: No relational integrity, complex structured queries
- Redis only: Memory limitations, no persistence guarantees

## 🎪 Decision

**DOPEMUX will implement a multi-level memory architecture** using specialized databases optimized for different data patterns and access requirements.

### Memory Layer Architecture

#### Layer 1: Cache Layer (Redis)
**Purpose**: Ultra-fast access for active session state
- **Use Cases**: Current context, agent coordination, real-time updates
- **Performance**: <10ms access times
- **Data Types**: Session state, active file states, agent assignments

#### Layer 2: Vector Database (Milvus)
**Purpose**: Semantic search and RAG capabilities
- **Use Cases**: Code similarity, documentation retrieval, pattern matching
- **Performance**: <100ms semantic queries
- **Data Types**: Code embeddings, documentation vectors, learned patterns

#### Layer 3: Relational Database (PostgreSQL)
**Purpose**: Structured data with ACID properties
- **Use Cases**: User settings, project metadata, audit trails
- **Performance**: <50ms for structured queries
- **Data Types**: User preferences, project configurations, decision history

#### Layer 4: Graph Database
**Purpose**: Relationship tracking and dependency analysis
- **Use Cases**: Code dependencies, agent interactions, knowledge graphs
- **Performance**: <200ms for complex traversals
- **Data Types**: Dependency relationships, interaction patterns, knowledge connections

#### Layer 5: Project Memory (ConPort)
**Purpose**: Project-specific context and decision tracking
- **Use Cases**: Architectural decisions, implementation patterns, project history
- **Performance**: <500ms for project context restoration
- **Data Types**: ADRs, code patterns, project-specific knowledge

#### Layer 6: Personal Memory (OpenMemory/0mem)
**Purpose**: Cross-session learning and personal accommodations
- **Use Cases**: ADHD patterns, personal preferences, learning history
- **Performance**: <100ms for preference queries
- **Data Types**: Attention patterns, successful strategies, personal configurations

### Integration Strategy

#### Query Routing
```python
class MemoryRouter:
    def route_query(self, query_type, context):
        if query_type == "current_context":
            return redis_client.get(context.session_id)
        elif query_type == "semantic_search":
            return milvus_client.search(context.embeddings)
        elif query_type == "user_preferences":
            return postgres_client.query_user_settings(context.user_id)
        elif query_type == "project_patterns":
            return conport_client.get_patterns(context.project_id)
        elif query_type == "personal_accommodations":
            return openmemory_client.get_adhd_patterns(context.user_id)
```

#### Data Synchronization
- **Event-driven updates**: Changes propagated across relevant layers
- **Consistency protocols**: Ensure data integrity across databases
- **Conflict resolution**: Handle competing updates gracefully

#### Backup Strategy
- **Layered backups**: Each database backed up according to its characteristics
- **Cross-reference integrity**: Maintain relationships across backups
- **Recovery procedures**: Layer-specific restoration processes

## 🔄 Consequences

### Positive
- ✅ **Optimized performance**: Each layer optimized for its use cases
- ✅ **Scalability**: Independent scaling of different data types
- ✅ **ADHD-friendly**: <500ms context restoration achieved
- ✅ **Rich capabilities**: Vector search, graph traversal, relational integrity
- ✅ **Fault tolerance**: Failure of one layer doesn't break entire system
- ✅ **Technology fit**: Right tool for each job
- ✅ **Future-proof**: Can add/modify layers as needs evolve

### Negative
- ❌ **Complexity**: Multiple databases to manage and maintain
- ❌ **Consistency challenges**: Keeping data synchronized across layers
- ❌ **Operational overhead**: Multiple backup/monitoring/maintenance processes
- ❌ **Development complexity**: More complex query routing and error handling
- ❌ **Resource usage**: Higher memory and storage requirements

### Neutral
- ℹ️ **Learning curve**: Team needs expertise across multiple database technologies
- ℹ️ **Deployment complexity**: Container orchestration required
- ℹ️ **Cost implications**: Multiple database licenses/hosting costs

## 🧠 ADHD Considerations

### Context Preservation Optimization
- **Layer prioritization**: Critical context in fastest layers (Redis)
- **Progressive loading**: Essential data first, detailed context on demand
- **Graceful degradation**: System works even if some layers unavailable

### Attention-Aware Access Patterns
- **Scattered attention**: Quick cache-based responses
- **Focused attention**: Deep semantic search across all layers
- **Hyperfocus**: Direct access to specialized data stores
- **Context switching**: Minimal latency between different memory types

### Memory Accommodation Features
- **Pattern recognition**: Graph database tracks successful ADHD strategies
- **Personal optimization**: OpenMemory learns individual accommodation needs
- **Context restoration**: Multi-layer approach enables <500ms restoration
- **Decision support**: Rich context from multiple sources reduces cognitive load

## 🔗 References
- [Multi-Level Memory Architecture](../HISTORICAL/preliminary-docs-normalized/docs/DOPEMUX_MEMORY_ARCHITECTURE.md)
- [Vector Database ADR](501-vector-database-milvus.md)
- [Cache Layer ADR](502-cache-layer-redis.md)
- [Relational Storage ADR](503-relational-storage-postgresql.md)
- [ConPort Integration ADR](505-conport-integration.md)
- [OpenMemory Integration ADR](506-openmemory-integration.md)
- [Memory Coordination Hub](../04-explanation/features/session-management.md)