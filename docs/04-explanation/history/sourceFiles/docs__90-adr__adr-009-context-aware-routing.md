# ADR-009: Context-Aware Memory Routing and Storage Strategy

**Status**: Proposed
**Date**: 2025-09-22
**Deciders**: Dopemux Team

## Context

The Intelligent Memory Layer will capture large volumes of development activities. Not all captured content has equal importance or requires the same storage treatment. We need a smart routing strategy that:

1. **Optimizes storage costs** (vector embeddings are expensive)
2. **Maintains retrieval performance** (important memories must be findable)
3. **Respects memory importance** (decisions more valuable than casual observations)
4. **Provides ADHD-specific prioritization** (what helps with context recovery?)

## Decision

We will implement **context-aware routing** that intelligently decides:

1. **What to store**: Importance-based filtering
2. **Where to store**: PostgreSQL vs PostgreSQL + Milvus
3. **How to process**: Full analysis vs lightweight processing
4. **When to surface**: Proactive retrieval triggers

Based on:
- **Content classification** (decision > task > observation)
- **Context importance** (main project files > scratch files)
- **User behavior patterns** (frequently accessed memories get priority)
- **ADHD-specific value** (context recovery importance)

## Rationale

### Storage Cost Optimization
Vector embeddings in Milvus require significant storage and compute:
- **1536 dimensions per embedding** (OpenAI text-embedding-3-small)
- **High-quality vectors expensive** to generate and store
- **Not all content needs semantic search** (e.g., trivial file changes)

Smart routing ensures only valuable content gets full vector treatment.

### ADHD-Specific Prioritization
Different memory types have different value for ADHD developers:

**High Priority** (Always vectorize):
- **Decisions**: "Why did we choose X?" queries are critical
- **Problems**: Needed for pattern recognition and debugging
- **Solutions**: Help avoid repeating problem-solving work

**Medium Priority** (Contextual vectorization):
- **Tasks**: Important if part of ongoing work
- **Observations**: Valuable if related to current focus area

**Low Priority** (Store but don't vectorize):
- **File changes**: Important for relationships but not semantic search
- **Trivial messages**: Keep for completeness but don't index

### Context-Aware Intelligence
Where and when something happens affects its importance:

**High-Value Contexts**:
- **Main source directories**: Core project code changes
- **Active work sessions**: Memories from current focus areas
- **Problem-solving periods**: Higher density of valuable decisions

**Lower-Value Contexts**:
- **Experimental directories**: Temporary exploration work
- **Documentation-only changes**: Less likely to need semantic search
- **Automated tool outputs**: Generated content with limited value

## Implementation Strategy

### Memory Importance Scoring
```python
class MemoryImportanceScorer:
    def calculate_importance(self, memory: ClassifiedMemory, context: Context) -> float:
        """Calculate 0-1 importance score for routing decisions"""

        score = 0.0

        # Base score by memory type
        type_scores = {
            MemoryType.DECISION: 0.9,
            MemoryType.PROBLEM: 0.8,
            MemoryType.SOLUTION: 0.8,
            MemoryType.TASK: 0.6,
            MemoryType.OBSERVATION: 0.4,
            MemoryType.QUESTION: 0.5,
        }
        score = type_scores.get(memory.type, 0.3)

        # Context boosts
        if context.is_main_project_file():
            score *= 1.3
        if context.is_active_work_session():
            score *= 1.2
        if context.has_recent_problems():  # Problem-solving context
            score *= 1.1

        # Content quality indicators
        if len(memory.text) > 100:  # Substantial content
            score *= 1.1
        if memory.confidence > 0.8:  # High classification confidence
            score *= 1.05

        # ADHD-specific boosts
        if memory.relates_to_context_switching():
            score *= 1.2  # Context recovery is crucial
        if memory.explains_reasoning():
            score *= 1.15  # "Why" answers are valuable

        return min(score, 1.0)
```

### Smart Routing Logic
```python
class ContextAwareRouter:
    def route_memory(self, memory: ClassifiedMemory, context: Context):
        """Decide storage and processing strategy"""

        importance = self.scorer.calculate_importance(memory, context)

        # Always store basic node information
        storage_plan = StoragePlan(
            store_node=True,
            create_relationships=True
        )

        # Routing decisions based on importance
        if importance >= 0.7:
            # High importance: Full treatment
            storage_plan.vectorize = True
            storage_plan.full_analysis = True
            storage_plan.proactive_surfacing = True

        elif importance >= 0.4:
            # Medium importance: Selective treatment
            storage_plan.vectorize = self.should_vectorize_medium(memory, context)
            storage_plan.full_analysis = True
            storage_plan.proactive_surfacing = False

        else:
            # Low importance: Minimal treatment
            storage_plan.vectorize = False
            storage_plan.full_analysis = False
            storage_plan.proactive_surfacing = False

        return storage_plan

    def should_vectorize_medium(self, memory: ClassifiedMemory, context: Context) -> bool:
        """Decide vectorization for medium-importance memories"""

        # Vectorize if related to current work
        if context.relates_to_current_branch():
            return True

        # Vectorize if user has searched for similar content recently
        if self.user_interest_detector.shows_interest_in(memory.topic):
            return True

        # Vectorize if part of ongoing conversation thread
        if memory.source == 'claude_message' and context.in_active_conversation():
            return True

        return False
```

### Context Detection
```python
class ContextAnalyzer:
    def analyze_context(self, event: Event) -> Context:
        """Enrich event with contextual information"""

        return Context(
            # Location context
            current_directory=os.getcwd(),
            current_branch=git.current_branch(),
            current_files=self.get_open_files(),

            # Temporal context
            session_duration=self.get_session_duration(),
            last_context_switch=self.get_last_context_switch(),
            recent_activity=self.get_recent_activity(minutes=30),

            # Work context
            is_main_project=self.is_main_project_directory(),
            is_experimental=self.is_experimental_directory(),
            active_conversation=self.get_active_conversation(),

            # ADHD context
            attention_state=self.get_attention_state(),
            focus_session_length=self.get_focus_session_length(),
            context_switch_frequency=self.get_context_switch_frequency()
        )
```

### Proactive Surfacing Strategy
```python
class ProactiveSurfacing:
    def should_surface(self, memory: ClassifiedMemory, current_context: Context) -> bool:
        """Decide when to proactively show memories"""

        # Surface high-importance memories on context changes
        if (memory.importance >= 0.7 and
            current_context.relates_to(memory.context) and
            current_context.is_context_switch()):
            return True

        # Surface problem/solution pairs when similar problems detected
        if (memory.type in [MemoryType.PROBLEM, MemoryType.SOLUTION] and
            current_context.has_similar_problem(memory)):
            return True

        # Surface decisions when related files are opened
        if (memory.type == MemoryType.DECISION and
            current_context.opened_files_relate_to(memory)):
            return True

        return False
```

## Benefits

### Storage Efficiency
- **~70% reduction** in vector storage by filtering low-value content
- **Faster retrieval** due to smaller, higher-quality vector space
- **Cost optimization** for cloud-based vector services
- **Scalable growth** as project history accumulates

### ADHD-Optimized Experience
- **Relevant context surfaces automatically** when switching files/directories
- **Decision context available** when working on related code
- **Problem patterns recognized** to prevent repeated struggles
- **Gentle memory prompts** without overwhelming information

### Performance Benefits
- **Faster searches** in curated vector space
- **Reduced processing overhead** for low-value content
- **Better relevance** in semantic search results
- **Optimized resource usage** for background processing

## Routing Decision Matrix

| Memory Type | Context | Importance | Store Node | Vectorize | Full Analysis | Proactive |
|-------------|---------|------------|------------|-----------|---------------|-----------|
| Decision    | Any     | High       | ✅         | ✅        | ✅            | ✅        |
| Problem     | Main    | High       | ✅         | ✅        | ✅            | ✅        |
| Solution    | Main    | High       | ✅         | ✅        | ✅            | ✅        |
| Task        | Active  | Medium     | ✅         | ✅        | ✅            | ❌        |
| Task        | Background | Low     | ✅         | ❌        | ❌            | ❌        |
| Observation | Related | Medium     | ✅         | Maybe     | ✅            | ❌        |
| File Change | Any     | Low        | ✅         | ❌        | ❌            | ❌        |

## Risks and Mitigations

### Over-Filtering
**Risk**: Important memories classified as low-value and not vectorized
**Mitigation**:
- Conservative importance thresholds
- User correction feedback to improve scoring
- Ability to retroactively vectorize memories

### Context Detection Accuracy
**Risk**: Poor context analysis leads to bad routing decisions
**Mitigation**:
- Multiple context signals for robustness
- Learning from user behavior patterns
- Explicit user feedback collection

### Storage Inconsistency
**Risk**: Related memories stored with different strategies, breaking relationships
**Mitigation**:
- Always store nodes and relationships regardless of vectorization
- Separate relationship discovery from storage decisions
- Monitoring for relationship completeness

## Consequences

### Positive
- **Cost-effective scaling** as memory volume grows
- **Better search relevance** through curated vector space
- **ADHD-optimized surfacing** based on context importance
- **Performance optimization** through selective processing

### Negative
- **Complex routing logic** increases system complexity
- **Potential for missed memories** if importance scoring is poor
- **Learning period required** for optimal context detection
- **More configuration options** for users to understand

## Alternatives Considered

### Store Everything Equally
- **Pros**: Simple, no risk of missing important memories
- **Cons**: High costs, poor search performance, overwhelming retrieval
- **Rejected**: Not sustainable as memory volume grows

### User-Defined Rules
- **Pros**: User has complete control over routing
- **Cons**: Cognitive overhead, manual configuration burden
- **Rejected**: Violates zero-effort principle for ADHD optimization

### Machine Learning Routing
- **Pros**: Could learn optimal patterns over time
- **Cons**: Requires training data, model maintenance complexity
- **Future Enhancement**: Could improve upon rule-based routing

## Success Metrics

- **Storage Efficiency**: 60-80% reduction in vector storage without losing search quality
- **Search Relevance**: >90% of important memories findable through semantic search
- **Context Accuracy**: Users find proactive surfacing helpful 80% of the time
- **Performance**: Sub-100ms search responses in production use

## Future Enhancements

1. **Learning from User Behavior**: Adapt importance scoring based on which memories users actually access
2. **Dynamic Context Weighting**: Adjust context importance based on user work patterns
3. **Collaborative Filtering**: Learn from team patterns about what memories are valuable
4. **Time-Based Importance Decay**: Reduce importance of old memories unless explicitly valuable

This context-aware routing strategy ensures that the Intelligent Memory Layer remains efficient and relevant while providing maximum value for ADHD-optimized development workflows.