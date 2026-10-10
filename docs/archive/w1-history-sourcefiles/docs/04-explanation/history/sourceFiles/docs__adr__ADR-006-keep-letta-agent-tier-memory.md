# ADR-006: Keep Letta for Agent-Tier Memory

**Status**: Accepted
**Date**: September 21, 2025
**Context**: RFC-001 Unified Memory Graph implementation

## Context

Letta provides working/recall/archival memory tiers and persistent state management; it's already chosen as our primary memory system for agent-level operations. Letta excels at managing ephemeral reasoning, context windows, and automatic eviction/summarization under memory pressure. ConPort serves a different purpose as project-level knowledge graph.

## Decision

Continue using Letta for per-agent memory tiers; ConPort remains project graph:

- **Agent Memory**: Letta handles working/recall/archival tiers for individual agents
- **Project Memory**: ConPort manages decisions, files, tasks, and relationships
- **Clear Separation**: Ephemeral reasoning vs long-term project knowledge
- **No Conflicts**: Each system optimized for its specific memory patterns

## Consequences

### Positive
- **Clean separation**: Avoids conflating ephemeral reasoning with long-term knowledge
- **Specialized optimization**: Each system designed for different memory patterns
- **Proven architecture**: Letta's tiered memory model is well-tested
- **Agent autonomy**: Agents maintain their own working memory independent of project state

### Negative
- **Multiple memory systems**: More components to coordinate and maintain
- **Potential overlap**: Some agent memories might be relevant to project knowledge
- **Coordination complexity**: Ensuring consistency between agent and project memory

### Mitigation
- Design clear interfaces for promoting agent insights to project memory
- Implement periodic sync between agent memories and project graph where relevant
- Use standardized memory events that both systems can consume