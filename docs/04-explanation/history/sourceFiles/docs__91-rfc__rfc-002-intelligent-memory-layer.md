# RFC-002: Intelligent Memory Layer for Implicit Context Preservation

**Status**: Draft
**Author**: Dopemux Team
**Created**: 2025-09-22
**Updated**: 2025-09-22

## Summary

This RFC proposes an Intelligent Memory Layer for Dopemux that automatically captures, classifies, and connects development activities without manual intervention. The system will transform the existing manual memory operations into a fully implicit workflow that preserves context, decisions, and relationships with zero cognitive overhead for ADHD developers.

## Motivation

### Current State

The Dopemux Unified Memory System successfully provides:
- ✅ Multi-database architecture (PostgreSQL + Milvus)
- ✅ HTTP API for memory operations
- ✅ Conversation history import capabilities
- ✅ Graph relationship management

However, the system requires **manual memory operations**:
- Developers must explicitly call `mem.upsert` for decisions
- Type classification must be manually specified
- Relationships require manual creation
- Context preservation depends on conscious effort

### The ADHD Challenge

For neurodivergent developers, manual memory management creates additional cognitive load precisely when attention is already strained. Key challenges include:

1. **Attention Fragmentation**: Stopping to manually record decisions interrupts flow state
2. **Inconsistent Capture**: Important context lost during hyperfocus or distraction periods
3. **Classification Burden**: Determining whether something is a "decision" vs "task" vs "observation" adds mental overhead
4. **Relationship Discovery**: Manually linking related entities requires working memory that ADHD developers often lack

### Vision: Zero-Effort Memory

The ideal ADHD-optimized memory system should:
- **Capture everything** automatically without interrupting workflow
- **Classify intelligently** based on content and context
- **Connect semantically** through relationship inference
- **Surface proactively** when context becomes relevant

## Detailed Design

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                EVENT SOURCES                    │
├─────────────┬─────────────┬─────────────────────┤
│ Git Hooks   │ Shell Cmds  │ Claude Messages     │
│ File Watcher│ Editor      │ Context Switches    │
└─────────────┴─────────────┴─────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│            CAPTURE LAYER (Instant)              │
│   • Universal Event Collector                  │
│   • Context Enrichment                         │
│   • Non-blocking Queue                         │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│        CLASSIFICATION LAYER (Hybrid)           │
│   Fast Path: Pattern Matching (<10ms)          │
│   Slow Path: AI Analysis (async)               │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│         ENRICHMENT LAYER                        │
│   • Relationship Inference                     │
│   • Metadata Extraction                        │
│   • Context Association                        │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│           STORAGE LAYER                         │
│   PostgreSQL + Milvus (existing)               │
│   Smart routing based on importance             │
└─────────────────────────────────────────────────┘
```

### Key Components

#### 1. Universal Event Collector
- **Zero-latency capture** from all sources
- **Context enrichment** with current state (branch, directory, session)
- **Async processing** to never block developer workflow

#### 2. Hybrid Classification Engine
- **Fast Pattern Matching**: Rule-based classification for common patterns (<10ms)
- **AI Classification**: LLM-powered analysis for complex cases (async)
- **Progressive Enhancement**: Works immediately, improves with AI

#### 3. Intelligent Relationship Builder
- **Temporal Proximity**: Links activities happening in sequence
- **File Associations**: Connects changes to the same files
- **Conversation Flow**: Maintains discussion context
- **Git Relationships**: Links commits to affected files

#### 4. Context-Aware Surfacing
- **Proactive Reminders**: Surfaces relevant context on file/directory changes
- **Break Recovery**: Helps restore context after interruptions
- **Morning Startup**: Provides yesterday's context summary

### Event Sources and Integration Points

#### Git Integration
```bash
# Post-commit hook (auto-installed)
#!/bin/bash
echo "$GIT_COMMIT_MESSAGE" | dopemux-capture git_commit &
```

#### Shell Integration
```bash
# Transparent command wrappers
cd() { dopemux-capture context_switch "$PWD→$1" & && builtin cd "$@"; }
pytest() { command pytest "$@" || dopemux-capture test_failure "$*" &; }
```

#### Claude Code Integration
```python
# Message hook for substantive conversations
async def on_message(msg):
    if len(msg.content) > 50:  # Skip trivial messages
        await dopemux_capture('claude_message', msg)
```

### Classification Logic

#### Memory Types
- **Decision**: "Let's use PostgreSQL", "Decided to refactor auth"
- **Task**: "Need to implement", "TODO: fix the bug"
- **Problem**: "This isn't working", "Error in production"
- **Solution**: "Fixed by changing", "Resolved the issue"
- **Observation**: "Interesting pattern", "Performance seems slow"
- **Question**: "Why does this happen?", "How should we approach?"

#### Classification Rules
1. **Context-First**: Source provides strong hints (git commit = likely decision)
2. **Pattern Matching**: Fast regex for common patterns
3. **AI Fallback**: LLM analysis for ambiguous cases
4. **Confidence Scoring**: Track classification accuracy over time

### Relationship Patterns

#### Automatic Relationships
- **Decision → Implementation**: Decision followed by file changes
- **Problem → Solution**: Problem description followed by fix
- **Question → Answer**: Question in conversation gets answered
- **Commit → Files**: Git commits automatically link to changed files
- **Test Failure → Code**: Failed tests link to source files

## Benefits

### For ADHD Developers
1. **Zero Cognitive Load**: No manual memory operations required
2. **Context Preservation**: Automatic capture during hyperfocus
3. **Recovery Support**: Easy context restoration after breaks/interruptions
4. **Decision Archaeology**: "Why did we choose X?" instantly answerable

### For Development Teams
1. **Institutional Memory**: Knowledge preserved across team members
2. **Onboarding Acceleration**: New team members see decision context
3. **Architecture Decisions**: Rationale maintained for future reference
4. **Code Understanding**: Files connected to their design decisions

### For Project Management
1. **Progress Tracking**: Automatic task/decision logging
2. **Risk Management**: Problems and solutions tracked
3. **Knowledge Transfer**: Context preserved across handoffs

## Implementation Strategy

### Phase 1: Core Pipeline (Week 1)
- Universal Event Collector daemon
- Fast pattern classification
- Basic git hook integration
- Simple storage routing

### Phase 2: AI Integration (Week 2)
- LLM classification service
- Extraction capabilities
- Relationship inference engine
- Confidence tracking

### Phase 3: Full Integration (Week 3)
- Shell command wrappers
- Claude Code message hooks
- File system watchers
- Context-aware surfacing

### Phase 4: Intelligence Enhancement (Week 4)
- Smart storage optimization
- Proactive context surfacing
- Learning from user corrections
- Performance optimization

## Risks and Mitigations

### Privacy Concerns
**Risk**: Sensitive information captured and processed
**Mitigation**: Local processing option, content filtering, user control over data sharing

### Performance Impact
**Risk**: Event capture slows down development workflow
**Mitigation**: <10ms capture guarantee, async processing, intelligent batching

### Classification Accuracy
**Risk**: AI misclassifies content, creating noise
**Mitigation**: Confidence scoring, pattern fallbacks, user correction feedback

### Storage Overhead
**Risk**: Too much data stored, expensive vector operations
**Mitigation**: Smart routing, importance scoring, selective vectorization

## Success Metrics

### Technical Metrics
- **Capture Latency**: <10ms for all events
- **Classification Accuracy**: >85% for common patterns
- **Storage Efficiency**: Only important items vectorized
- **Relationship Precision**: >80% auto-relationships are valuable

### User Experience Metrics
- **Zero Manual Operations**: No explicit memory commands needed
- **Context Recovery**: <30 seconds to restore working context
- **Decision Discovery**: <5 seconds to find "why we chose X"
- **Attention Preservation**: No workflow interruptions for memory

### ADHD-Specific Metrics
- **Context Switch Recovery**: Relevant memories surfaced automatically
- **Break Continuity**: Smooth resumption after interruptions
- **Hyperfocus Support**: Complete capture during intense focus
- **Cognitive Load**: Measured reduction in memory-related mental effort

## Future Enhancements

### Advanced Intelligence
- **Learning from Corrections**: Improve classification based on user feedback
- **Team Patterns**: Learn project-specific classification patterns
- **Temporal Analysis**: Understand typical development cycles and patterns

### Enhanced Integration
- **IDE Plugins**: Direct editor integration for richer context
- **Calendar Integration**: Link development work to meetings/planning
- **Issue Tracker Sync**: Connect decisions to tickets and requirements

### Multi-Modal Memory
- **Visual Context**: Screenshot capture for design decisions
- **Audio Notes**: Voice memo integration for quick thoughts
- **Diagram Association**: Link architectural diagrams to decisions

## Conclusion

The Intelligent Memory Layer transforms Dopemux from a powerful but manual memory system into a truly implicit cognitive enhancement tool. By capturing everything automatically and intelligently classifying content, we eliminate the cognitive overhead that prevents ADHD developers from maintaining comprehensive project memory.

This system respects the neurodivergent attention patterns while providing the memory support that enables sustained focus and creative problem-solving. The result is a development environment that learns and remembers, freeing developers to focus on what they do best: creating solutions.

## References

- [Dopemux Unified Memory Implementation](../UNIFIED_MEMORY_IMPLEMENTATION.md)
- [ADHD and Working Memory Research](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6379043/)
- [Context Switching in Software Development](https://www.petrikainulainen.net/software-development/processes/the-cost-of-context-switching/)
- [Attention Restoration Theory](https://en.wikipedia.org/wiki/Attention_restoration_theory)