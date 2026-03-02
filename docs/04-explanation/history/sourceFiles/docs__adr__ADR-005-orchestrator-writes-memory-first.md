# ADR-005: Orchestrator Writes Through Memory First

**Status**: Accepted
**Date**: September 21, 2025
**Context**: RFC-001 Unified Memory Graph implementation

## Context

MCP servers are first-class citizens in our architecture; ConPort is our designated memory MCP. The multi-LLM chat window serves as the primary orchestrator for development workflows. We need to ensure all interactions are captured for project understanding, debugging, and future reference. Writing to memory first ensures we have a complete audit trail of all decisions and actions.

## Decision

Multi-LLM chat window emits events → mem.upsert/graph.link before any downstream actions:

- **Event-Driven**: Every user message, assistant response, and tool call generates memory events
- **Memory First**: All events written to ConPort before triggering downstream actions
- **Atomic Operations**: Memory writes and subsequent actions succeed/fail together
- **Audit Trail**: Complete record of what led to every system change

## Consequences

### Positive
- **Durable, queryable history**: Never lose context of why decisions were made
- **Deterministic behavior**: Can replay and understand system state changes
- **Debugging capability**: Full trace from user intent to system action
- **Project knowledge**: Builds comprehensive understanding over time

### Negative
- **Performance overhead**: Memory write latency affects response time
- **Complexity**: Must handle memory write failures gracefully
- **Storage growth**: All interactions stored permanently

### Mitigation
- Implement async memory writes where possible
- Use connection pooling and caching for memory operations
- Implement archival strategy for old conversations
- Design graceful degradation when memory system unavailable