# ADR-503: Relational Storage (PostgreSQL)

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX memory architecture team
**Tags**: #critical #database #postgresql #structured-data

## 🎯 Context

DOPEMUX requires robust relational storage for structured data that demands ACID properties, complex queries, and long-term persistence. While Redis handles fast cache access and Milvus handles vector search, structured application data needs traditional relational database capabilities.

### Structured Data Requirements
- **User management**: Accounts, preferences, ADHD accommodation settings
- **Project metadata**: Project configurations, team assignments, permissions
- **Audit trails**: Decision history, change logs, compliance tracking
- **Configuration data**: System settings, feature flags, integration configs
- **Metrics and analytics**: Usage statistics, performance measurements, user feedback
- **Workflow state**: Task progression, milestone tracking, approval workflows

### Relational Database Needs
- **ACID transactions**: Ensure data consistency across complex operations
- **Complex queries**: Join multiple tables for comprehensive reporting
- **Data integrity**: Foreign key constraints and referential integrity
- **Concurrent access**: Multiple users and agents accessing shared data
- **Backup and recovery**: Enterprise-grade data protection
- **Performance**: Sub-50ms queries for structured data operations

### Database Technology Options
1. **PostgreSQL**: Advanced open-source relational database
2. **MySQL**: Popular open-source database
3. **SQLite**: Embedded database for simpler deployments
4. **CockroachDB**: Distributed SQL database
5. **MariaDB**: MySQL fork with additional features

### Key Decision Factors
- **ACID compliance**: Full transaction support for critical operations
- **JSON support**: Handle semi-structured data within relational model
- **Performance**: Excellent query optimization and indexing
- **Extensibility**: Plugin architecture for future enhancements
- **Standards compliance**: Full SQL standard support
- **Open source**: No licensing restrictions for distribution

## 🎪 Decision

**DOPEMUX will use PostgreSQL as the primary relational database** for structured data storage.

### Technical Configuration
- **Version**: PostgreSQL 15+ for latest performance improvements
- **Connection pooling**: PgBouncer for efficient connection management
- **Extensions**: Enable JSON/JSONB, UUID, and full-text search extensions
- **Backup strategy**: Continuous WAL archiving with point-in-time recovery
- **Performance tuning**: Optimized for OLTP workloads with read replicas for analytics

### Schema Design Strategy
```sql
-- Core entity organization
USERS
├── user_id (UUID, primary key)
├── email (unique, not null)
├── adhd_profile (JSONB)
├── preferences (JSONB)
└── created_at, updated_at

PROJECTS
├── project_id (UUID, primary key)
├── name, description
├── owner_id (FK to users)
├── configuration (JSONB)
├── memory_settings (JSONB)
└── created_at, updated_at

SESSIONS
├── session_id (UUID, primary key)
├── user_id (FK to users)
├── project_id (FK to projects)
├── metadata (JSONB)
├── started_at, ended_at
└── archived_at

DECISIONS
├── decision_id (UUID, primary key)
├── session_id (FK to sessions)
├── decision_type, context
├── alternatives (JSONB)
├── rationale (TEXT)
└── timestamp
```

### Data Access Patterns
- **User operations**: Authentication, preferences, ADHD settings
- **Project queries**: Configuration retrieval, team member access
- **Audit queries**: Decision history, change tracking, compliance reports
- **Analytics queries**: Usage patterns, performance metrics, user behavior
- **Configuration management**: Feature flags, system settings, integration configs

### Performance Optimizations
- **Indexing strategy**: B-tree indexes for common queries, GIN indexes for JSONB
- **Partitioning**: Partition large tables by date or user for better performance
- **Query optimization**: Use EXPLAIN ANALYZE for query tuning
- **Connection pooling**: Limit concurrent connections and reuse connections
- **Read replicas**: Separate read workloads from write operations

## 🔄 Consequences

### Positive
- ✅ **Data integrity**: ACID transactions ensure consistent data state
- ✅ **Complex queries**: Rich SQL support for sophisticated data operations
- ✅ **JSON flexibility**: JSONB support for semi-structured data
- ✅ **Performance**: Excellent query optimization and indexing capabilities
- ✅ **Reliability**: Enterprise-grade backup, recovery, and replication
- ✅ **Standards compliance**: Full SQL standard ensures portability
- ✅ **Extensibility**: Rich plugin ecosystem for future enhancements
- ✅ **Community support**: Large, active community and extensive documentation

### Negative
- ❌ **Resource overhead**: Higher memory and CPU usage than simpler databases
- ❌ **Operational complexity**: Requires database administration expertise
- ❌ **Scaling limitations**: Vertical scaling has practical limits
- ❌ **Query performance**: Can be slower than specialized databases for specific use cases

### Neutral
- ℹ️ **Learning curve**: Team needs PostgreSQL-specific knowledge
- ℹ️ **Administration overhead**: Database tuning, maintenance, and monitoring required
- ℹ️ **Backup complexity**: More sophisticated backup/recovery procedures needed

## 🧠 ADHD Considerations

### User Experience Optimization
- **Preference persistence**: Reliable storage of ADHD accommodation settings
- **Configuration reliability**: Ensure user customizations never lost
- **Progress tracking**: Accurate milestone and achievement records
- **Pattern learning**: Store successful strategies and adaptation patterns

### Performance for ADHD Workflows
- **Quick preference access**: <50ms retrieval of user settings
- **Reliable session tracking**: Accurate progress and state persistence
- **History preservation**: Complete audit trail for reflection and learning
- **Error recovery**: Transaction rollback for gentle error handling

### Data Privacy and Security
- **ADHD data protection**: Secure storage of sensitive neurodivergent information
- **Access controls**: Fine-grained permissions for personal data
- **Audit compliance**: Complete change tracking for sensitive operations
- **Data sovereignty**: Local storage options for privacy-conscious users

### Integration with ADHD Features
- **Accommodation storage**: Persistent ADHD preference and adaptation data
- **Progress analytics**: Track productivity patterns and successful strategies
- **Decision history**: Learn from past choices to reduce future cognitive load
- **Pattern recognition**: Identify and store successful workflow patterns

## 🔗 References
- [Multi-Level Memory Architecture](003-multi-level-memory-architecture.md)
- [Cache Layer Strategy](502-cache-layer-redis.md)
- [Data & Security ADRs](../90-adr/README.md#data--security-500-599)
- [User Experience Design](../04-explanation/adhd/gentle-ux.md)
- [Privacy and Security Model](../94-architecture/08-concepts/security.md)
- PostgreSQL Documentation: Performance tuning, JSONB operations, and indexing strategies