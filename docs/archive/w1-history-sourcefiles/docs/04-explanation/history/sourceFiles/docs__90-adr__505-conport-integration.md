# ADR-505: ConPort Integration

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX memory architecture team
**Tags**: #critical #integration #conport #project-memory

## 🎯 Context

DOPEMUX requires project-specific memory management that captures architectural decisions, implementation patterns, and contextual knowledge unique to each codebase. This project-level memory needs to persist across sessions and be accessible to all agents working on the project.

### Project Memory Requirements
- **Architectural decisions**: Design choices, patterns, and rationale
- **Implementation context**: Code patterns, successful approaches, lessons learned
- **Project-specific knowledge**: Domain understanding, business logic, constraints
- **Team collaboration**: Shared decisions, conventions, and agreements
- **Evolution tracking**: How the project has changed over time
- **Context handoffs**: Seamless knowledge transfer between development sessions

### ConPort Capabilities Analysis
ConPort (Context Porter) provides:
- **Project-scoped memory**: Isolated context per project
- **Decision tracking**: Formal recording of choices and rationale
- **Pattern storage**: Reusable code and architectural patterns
- **Context versioning**: Track evolution of project understanding
- **Agent coordination**: Shared knowledge base for multi-agent workflows
- **Query interface**: Intelligent retrieval of relevant project context

### Integration Requirements
- **Seamless access**: Agents can query project memory without friction
- **Real-time updates**: Changes immediately available to all agents
- **Context preservation**: Project knowledge survives system restarts
- **Privacy control**: Project-specific data remains isolated
- **Performance**: <200ms query response for context retrieval
- **Reliability**: Never lose critical project decisions and patterns

## 🎪 Decision

**DOPEMUX will integrate ConPort as the project memory management system** for persistent, project-scoped context and decision tracking.

### Integration Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Agent Query     │───►│ ConPort Client  │───►│ ConPort Server  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────▼─────────┐
│ Context Results │◄───│ Response Format │◄───│ Project Context  │
└─────────────────┘    └─────────────────┘    └─────────────────────┘
```

### Data Organization in ConPort
- **`decisions/`**: Architectural decisions with full context and rationale
- **`patterns/`**: Successful code patterns and implementation approaches
- **`context/`**: Domain knowledge, business rules, and project constraints
- **`evolution/`**: Change history and learning from past decisions
- **`conventions/`**: Team agreements, coding standards, and practices

### Agent Integration Points

#### Research Agent
```python
# Query existing project patterns before suggesting new approaches
existing_patterns = conport.query_patterns(domain="authentication")
research_context = conport.get_context(topic="security_requirements")
```

#### Implementation Agent
```python
# Store successful implementation patterns
conport.store_pattern(
    name="api_error_handling",
    code=implementation_code,
    rationale="Provides consistent error responses across all endpoints",
    tags=["error-handling", "api", "consistency"]
)
```

#### Decision Tracking
```python
# Record architectural decisions automatically
conport.record_decision(
    type="architecture",
    decision="use_microservices_architecture",
    context="Team discussion on scalability requirements",
    alternatives=["monolith", "modular_monolith"],
    rationale="Better team autonomy and technology diversity",
    trade_offs={"complexity": "higher", "deployment": "more complex"}
)
```

### Performance Optimizations
- **Local caching**: Frequently accessed patterns cached in Redis
- **Batch queries**: Multiple context requests combined efficiently
- **Incremental updates**: Only sync changes since last access
- **Smart prefetching**: Anticipate needed context based on current work

## 🔄 Consequences

### Positive
- ✅ **Project continuity**: Context preserved across sessions and team members
- ✅ **Decision transparency**: Clear record of why choices were made
- ✅ **Pattern reuse**: Successful approaches automatically available
- ✅ **Knowledge sharing**: Team knowledge captured and accessible
- ✅ **Context-aware development**: Agents understand project-specific patterns
- ✅ **Reduced repetition**: Avoid re-solving the same problems
- ✅ **Onboarding acceleration**: New team members access institutional knowledge
- ✅ **Quality consistency**: Established patterns promote consistent implementation

### Negative
- ❌ **External dependency**: Reliance on ConPort service availability
- ❌ **Data governance**: Need policies for what gets stored and for how long
- ❌ **Privacy concerns**: Sensitive project information in external service
- ❌ **Storage costs**: Large projects may require significant storage
- ❌ **Query complexity**: Learning optimal query patterns takes time

### Neutral
- ℹ️ **Integration complexity**: Additional API and error handling required
- ℹ️ **Data migration**: Existing project knowledge needs manual capture
- ℹ️ **Access control**: Need proper authentication and authorization

## 🧠 ADHD Considerations

### Cognitive Load Reduction
- **Automatic context**: Relevant project knowledge surfaced without explicit search
- **Decision history**: Understand why past choices were made without archaeology
- **Pattern recognition**: Identify similar problems and proven solutions
- **Context restoration**: Quickly understand project state after breaks

### Memory Augmentation
- **Institutional memory**: Project knowledge doesn't depend on individual recall
- **Learning reinforcement**: Successful patterns automatically reinforced
- **Decision support**: Previous decisions provide guidance for new choices
- **Context bridging**: Connect current work to related past decisions

### Attention-Friendly Features
- **Smart suggestions**: Proactively surface relevant context during development
- **Progressive disclosure**: Essential context first, details available on demand
- **Visual context**: Clear indicators of relevant patterns and decisions
- **Seamless integration**: Context appears naturally in development workflow

### Focus Protection
- **Minimal interruption**: Context retrieval happens transparently
- **Relevant filtering**: Only show context that matches current work
- **Attention preservation**: Quick access prevents context-switching overhead
- **Flow maintenance**: Information appears when needed without breaking focus

## 🔗 References
- [Multi-Level Memory Architecture](003-multi-level-memory-architecture.md)
- [OpenMemory Integration](506-openmemory-integration.md)
- [Project Memory Architecture](../HISTORICAL/preliminary-docs-normalized/docs/DOPEMUX_MEMORY_ARCHITECTURE.md)
- [Agent Coordination Patterns](../04-explanation/patterns/agent-coordination.md)
- [Decision Making Support](../04-explanation/adhd/executive-function.md)
- ConPort Documentation: API reference and integration patterns