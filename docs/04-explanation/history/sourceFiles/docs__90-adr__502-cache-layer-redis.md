# ADR-502: Cache Layer Strategy (Redis)

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX memory architecture team
**Tags**: #critical #performance #cache #redis #adhd

## 🎯 Context

DOPEMUX requires ultra-fast access to active session state and context for ADHD-friendly development workflows. Context switching and attention interruptions require sub-10ms access to current state to minimize cognitive disruption.

### Performance Requirements for ADHD Users
- **Context restoration**: <500ms total, <10ms for active session state
- **Real-time coordination**: Agent handoffs without perceptible delay
- **Attention preservation**: Immediate response to maintain focus flow
- **Session persistence**: Survive terminal crashes and network interruptions
- **Multi-agent sync**: Coordinate state updates across agents in real-time

### Cache Requirements Analysis
- **Session state**: Current files, cursor positions, active tasks
- **Agent coordination**: Active agent assignments, handoff state
- **User preferences**: ADHD accommodations, interface settings
- **Temporary context**: In-progress computations, draft decisions
- **Real-time metrics**: Attention state, focus duration, break timers

### Cache Technology Options
1. **Redis**: In-memory data structure store
2. **Memcached**: High-performance caching system
3. **In-process cache**: Application-level caching (e.g., LRU cache)
4. **File-based cache**: Fast file system cache
5. **Database caching**: PostgreSQL/SQLite caching layers

### Key Decision Factors
- **Performance**: <10ms access times for session state
- **Persistence**: Survive application restarts
- **Data structures**: Support for complex data types (hashes, lists, sets)
- **Atomic operations**: Consistent updates across multiple keys
- **Expiration**: Automatic cleanup of stale data
- **Clustering**: Scale across multiple instances if needed

## 🎪 Decision

**DOPEMUX will use Redis as the primary cache layer** for ultra-fast session state and real-time coordination.

### Technical Configuration
- **Persistence mode**: AOF (Append Only File) with 1-second fsync
- **Memory policy**: allkeys-lru for automatic eviction
- **Data structures**: Hashes for session state, lists for agent queues, sets for coordination
- **TTL strategy**: Session data expires after 24 hours of inactivity
- **Connection pooling**: Multiple connections for concurrent access

### Cache Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Session Manager │───►│ Redis Cache     │◄───│ Agent Coord     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                       ┌───────▼───────┐
                       │ Backup Layer  │
                       │ (PostgreSQL)  │
                       └───────────────┘
```

### Data Organization Strategy

#### Session State (Primary Cache)
```redis
session:{session_id}:state = {
    "current_files": ["file1.py", "file2.ts"],
    "cursor_positions": {"file1.py": [45, 12]},
    "active_task": "implement-auth",
    "attention_state": "focused",
    "last_update": timestamp
}
```

#### Agent Coordination
```redis
session:{session_id}:agents = {
    "primary_agent": "claude-code",
    "active_agents": ["researcher", "implementer"],
    "handoff_queue": [],
    "coordination_state": "parallel_work"
}
```

#### ADHD Context
```redis
user:{user_id}:adhd = {
    "current_attention": "focused",
    "focus_start_time": timestamp,
    "break_due": timestamp,
    "accommodation_level": "high",
    "notification_batch": []
}
```

### Performance Optimizations
- **Pipeline operations**: Batch multiple commands for efficiency
- **Lua scripts**: Atomic operations for complex state updates
- **Memory optimization**: Compress large values, use appropriate data types
- **Connection reuse**: Persistent connections with pooling
- **Hot key detection**: Monitor and optimize frequently accessed keys

## 🔄 Consequences

### Positive
- ✅ **Ultra-fast access**: <10ms response times for session state
- ✅ **ADHD-friendly**: Immediate context restoration without attention disruption
- ✅ **Rich data types**: Native support for complex session structures
- ✅ **Atomic operations**: Consistent state updates across concurrent access
- ✅ **Persistence**: Survive application crashes and restarts
- ✅ **Real-time coordination**: Instant agent synchronization
- ✅ **Automatic cleanup**: TTL-based expiration prevents memory bloat
- ✅ **Battle-tested**: Proven performance in high-load applications

### Negative
- ❌ **Memory dependency**: Requires sufficient RAM for all cached data
- ❌ **Single point of failure**: Cache unavailability impacts performance
- ❌ **Memory cost**: Higher resource usage than disk-based storage
- ❌ **Data volatility**: Risk of data loss without proper persistence
- ❌ **Network dependency**: Additional network hop for cache access

### Neutral
- ℹ️ **Operational complexity**: Another service to monitor and maintain
- ℹ️ **Memory management**: Need to tune memory policies and limits
- ℹ️ **Backup strategy**: Cache data needs backup/recovery procedures

## 🧠 ADHD Considerations

### Attention Preservation
- **Instant response**: <10ms access prevents attention drift during context switching
- **Seamless handoffs**: Agent coordination happens transparently
- **Focus protection**: No perceptible delays during development flow
- **Context integrity**: Session state never lost during focus sessions

### Cognitive Load Optimization
- **Transparent caching**: Users never wait for cache operations
- **Smart prefetching**: Anticipate needed context based on patterns
- **Memory augmentation**: Cache frequently used patterns and decisions
- **Interruption recovery**: Immediate restoration after attention breaks

### Accommodation Features
- **Personalized settings**: Cache individual ADHD accommodation preferences
- **Attention tracking**: Real-time attention state monitoring and adaptation
- **Break management**: Automatic break reminders based on cached timers
- **Gentle transitions**: Smooth state changes without jarring updates

### Integration with ADHD Workflow
- **Focus session support**: Track and maintain focus session state
- **Pattern learning**: Cache successful ADHD strategies and preferences
- **Decision support**: Store and retrieve decision context quickly
- **Progress tracking**: Real-time progress indicators without database queries

## 🔗 References
- [Multi-Level Memory Architecture](003-multi-level-memory-architecture.md)
- [ADHD Context Preservation](../04-explanation/adhd/context-theory.md)
- [Session Management Hub](../04-explanation/features/session-management.md)
- [Performance Requirements](../94-architecture/10-quality-requirements/performance.md)
- [Context Management Research](../HISTORICAL/preliminary-docs-normalized/research/findings/context-management-redis-caching.md)
- Redis Documentation: Persistence, memory optimization, and data structures