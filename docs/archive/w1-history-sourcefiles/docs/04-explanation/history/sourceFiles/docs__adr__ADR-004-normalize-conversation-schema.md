# ADR-004: Normalize Conversation Schema Across Tools

**Status**: Accepted
**Date**: September 21, 2025
**Context**: RFC-001 Unified Memory Graph implementation

## Context

Our documentation recommends unified storage for chat histories and embeddings across development tools. We have multiple sources of conversational data: Claude Code sessions, Codex CLI interactions, and multi-LLM chat. These need to be ingested into the unified memory system for comprehensive project understanding and semantic search.

## Decision

Use a JSONL schema for message, decision, run; import Claude Code & Codex CLI:

```json
{"type":"message","id":"...","role":"user|assistant|tool","thread":"...","text":"...","ts":...,"source":"claude-code|codex-cli","meta":{...}}
{"type":"decision","id":"...","text":"...","links":[{"rel":"affects","to":"file:src/foo.ts"}],"ts":...}
{"type":"run","id":"...","command":"...","output":"...","ts":...,"source":"codex-cli"}
```

**Import Process**:
1. Parse tool logs into normalized JSONL format
2. For each line: `mem.upsert` (both graph and vectors)
3. For decisions/files/tasks: `graph.link` to establish relationships

## Consequences

### Positive
- **Easy ingestion**: JSONL format simple to parse and process
- **Consistent analytics**: All conversation data queryable with same schema
- **Tool agnostic**: Works with any tool that can export structured logs
- **Incremental processing**: Can process logs in batches or real-time

### Negative
- **Format constraints**: Must map diverse tool outputs to common schema
- **Loss of nuance**: Some tool-specific metadata may not fit cleanly
- **Migration effort**: Existing logs need transformation to new format

### Mitigation
- Design flexible metadata field to capture tool-specific information
- Create comprehensive importers for each major tool
- Implement validation to ensure data quality during import