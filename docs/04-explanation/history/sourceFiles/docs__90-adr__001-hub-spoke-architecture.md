# ADR-001: Hub-and-Spoke Architecture Pattern

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX architecture team
**Tags**: #critical #architecture #core

## 🎯 Context

DOPEMUX requires a multi-agent orchestration pattern to coordinate different AI services while maintaining clarity and performance. Research analysis of production systems revealed significant differences in performance between orchestration patterns.

### Options Considered
1. **Mesh Architecture**: Every agent communicates with every other agent
2. **Chain Architecture**: Sequential agent handoffs in a linear chain
3. **Hub-and-Spoke Architecture**: Central orchestrator with spoke agents
4. **Hierarchical Architecture**: Multi-level agent management

### Research Validation
- Hub-and-spoke outperformed mesh architectures for development workflows
- Production systems using hub-and-spoke achieved 3x performance improvements
- Reduced complexity and token overhead compared to mesh patterns
- Better context preservation through centralized state management

## 🎪 Decision

**DOPEMUX will implement a hub-and-spoke architecture** with the CLI as the central orchestrator managing all agent interactions.

### Key Components
- **Central Hub**: DOPEMUX CLI coordinates all agent interactions
- **Spoke Agents**: Specialized AI services (Claude Code, MCP servers, etc.)
- **Deterministic Routing**: Clear handoff rules with complete context preservation
- **Token Budget Management**: Intelligent allocation with real-time monitoring

### Implementation Pattern
```
    CLI (Hub)
   /    |    \
Agent1 Agent2 Agent3
  |      |      |
Context Context Context
```

## 🔄 Consequences

### Positive
- ✅ **Simplified complexity**: Clear communication patterns
- ✅ **Better context preservation**: Central state management
- ✅ **Performance**: 3x improvement validated in production
- ✅ **Deterministic behavior**: Predictable agent handoffs
- ✅ **Easier debugging**: Central coordination point
- ✅ **Token efficiency**: Reduced overhead from mesh communication

### Negative
- ❌ **Single point of failure**: CLI orchestrator becomes critical
- ❌ **Scaling limitations**: Hub may become bottleneck at extreme scale
- ❌ **Development complexity**: More orchestration logic in central hub

### Neutral
- ℹ️ **Alternative patterns available**: Can switch to mesh for specific use cases
- ℹ️ **Gradual migration**: Can evolve architecture as needs change

## 🔗 References
- [DOPEMUX Technical Architecture v3](../HISTORICAL/preliminary-docs-normalized/docs/DOPEMUX_TECHNICAL_ARCHITECTURE_v3.md)
- [Hub-and-Spoke Explanation](../04-explanation/architecture/hub-spoke.md)
- [System Architecture Overview](../94-architecture/01-introduction-goals/system-overview.md)
- Production validation data: 3x performance improvement, 70-90% API cost savings