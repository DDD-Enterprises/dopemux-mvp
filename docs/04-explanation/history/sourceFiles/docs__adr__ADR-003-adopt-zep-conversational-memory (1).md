# ADR-003: Adopt Zep for Conversational Memory (Now)

**Status**: Accepted
**Date**: September 21, 2025
**Context**: RFC-001 Unified Memory Graph implementation

## Context

Zep offers chat memory, summaries, and embeddings functionality, recommended in our materials for conversational AI applications. We need immediate conversational memory for the multi-LLM chat interface while building out the project memory graph. Zep provides mature chat session management, automatic summarization, and vector search capabilities.

## Decision

Zep backs the multi-LLM chat pane; promoted decisions flow to ConPort:

- **Chat Memory**: Zep stores conversation turns, generates summaries, provides vector search
- **Project Memory**: ConPort handles decisions, tasks, files, and their relationships
- **Data Flow**: Conversations → Zep (immediate UX) → ConPort (promoted artifacts)
- **Clear Separation**: Chat memory vs project knowledge graph

## Consequences

### Positive
- **Immediate UX improvement**: Functional conversational memory without waiting for full graph implementation
- **No coupling**: Chat memory system independent of project graph evolution
- **Mature functionality**: Zep provides battle-tested chat memory features
- **Quick wins**: Can implement conversational features rapidly

### Negative
- **Additional system**: Another service to deploy, monitor, and maintain
- **Data duplication**: Some overlap between Zep conversations and ConPort messages
- **Integration complexity**: Need to handle promotion from chat to project memory

### Mitigation
- Implement clear promotion rules for moving important chat content to project graph
- Use nightly/periodic sync jobs to align Zep and ConPort data where needed
- Design promotion interface that's transparent to users