# ADR-007: Hybrid Classification Approach for Memory Intelligence

**Status**: Proposed
**Date**: 2025-09-22
**Deciders**: Dopemux Team

## Context

The Intelligent Memory Layer needs to automatically classify captured content into memory types (decision, task, problem, solution, etc.) without manual intervention. The classification must be:

1. **Fast enough** to not interrupt developer workflow (<10ms for common cases)
2. **Accurate enough** to be useful (>85% accuracy)
3. **Comprehensive enough** to handle nuanced content
4. **Cost-effective** for continuous operation

## Decision

We will implement a **hybrid classification approach** combining:

1. **Fast Pattern Matching** (local, <10ms): Rule-based classification for common patterns
2. **AI Classification** (async): LLM-powered analysis for complex/ambiguous cases
3. **Progressive Enhancement**: System works immediately with patterns, improves with AI

## Rationale

### Performance Requirements
- **ADHD developers cannot tolerate workflow interruption**
- Pattern matching provides <10ms classification for 70% of cases
- AI processing runs asynchronously, never blocking capture
- Immediate visual feedback possible with pattern-based classification

### Accuracy Balance
- **Simple patterns handle obvious cases reliably**:
  - Git commit starting with "feat:" → Decision
  - Text containing "TODO:" → Task
  - Text containing "Why does..." → Question
- **AI handles nuanced cases that patterns miss**:
  - "I think we should probably use PostgreSQL here" → Decision (subtle)
  - "The auth system seems fragile" → Observation (ambiguous)

### Cost Optimization
- **Pattern matching is free** (runs locally)
- **AI only processes complex cases** (~30% of content)
- **Local LLM option** for privacy-sensitive environments
- **Batch processing** for efficiency when using external APIs

### Flexibility
- **Easy to add new patterns** based on project-specific language
- **AI model can be swapped** (Ollama local → OpenAI → Anthropic)
- **Fallback gracefully** if AI service unavailable
- **Learning from corrections** improves both patterns and AI prompts

## Implementation Details

### Fast Pattern Classification
```python
class FastPatternClassifier:
    DECISION_PATTERNS = [
        r"(?i)\b(decided?|chose|going with|let's use)\b",
        r"(?i)^(feat|feature):\s*",  # Commit patterns
        r"(?i)\b(switched to|migrated to|adopted)\b",
    ]

    def classify(self, text: str, context: dict) -> Optional[MemoryType]:
        # Context provides strong hints
        if context['source'] == 'git_commit':
            if re.search(r'^feat:', text):
                return MemoryType.DECISION

        # Check content patterns
        for pattern in self.DECISION_PATTERNS:
            if re.search(pattern, text):
                return MemoryType.DECISION

        return None  # Needs AI classification
```

### AI Classification Service
```python
class AIClassifier:
    async def classify_with_extraction(self, content: str, context: dict):
        prompt = f"""
        Analyze this development activity:
        Source: {context['source']}
        Content: {content}

        Classify as: decision|task|problem|solution|observation|question
        Extract: entities, priority, relationships
        Return: JSON with classification and metadata
        """

        return await self.llm.extract_structured(prompt)
```

### Processing Flow
```
Event Captured → Context Analysis → Fast Patterns → Classified?
                                        ↓ No
                                   Queue for AI → AI Analysis → Classified
```

## Consequences

### Positive
- **Zero-latency experience** for common cases
- **High accuracy** for nuanced content through AI
- **Cost-effective** by using AI selectively
- **Offline capable** with pattern-only mode
- **Easily extensible** with new patterns or AI models

### Negative
- **Dual codepath complexity** (patterns + AI)
- **Potential inconsistency** between pattern and AI classification
- **AI dependency** for best accuracy
- **Pattern maintenance overhead** as language evolves

### Risks and Mitigations

**Risk**: Pattern and AI classifiers disagree
**Mitigation**: Confidence scoring, AI overrides patterns when confidence high

**Risk**: Pattern maintenance becomes burdensome
**Mitigation**: Use AI to suggest new patterns based on missed classifications

**Risk**: AI service outages affect classification quality
**Mitigation**: Graceful degradation to pattern-only mode with user notification

## Alternatives Considered

### Pure AI Classification
- **Pros**: Highest accuracy, handles all nuances
- **Cons**: Latency issues, cost concerns, dependency on external services
- **Rejected**: Cannot meet <10ms requirement for ADHD workflow

### Pure Pattern Matching
- **Pros**: Fastest, no dependencies, completely local
- **Cons**: Limited accuracy for subtle cases, high maintenance overhead
- **Rejected**: Insufficient accuracy for complex development language

### Machine Learning Classification
- **Pros**: Fast inference, learns project patterns
- **Cons**: Training data requirements, model maintenance complexity
- **Deferred**: Could be future enhancement once we have training data

## Success Metrics

- **Classification Speed**: >70% of events classified in <10ms
- **Pattern Accuracy**: >90% accuracy for pattern-matched classifications
- **AI Accuracy**: >95% accuracy for AI-processed classifications
- **Coverage**: <5% of events remain unclassified
- **User Satisfaction**: Developers report classifications feel "natural"

## Future Evolution

1. **Pattern Learning**: Use AI to suggest new patterns from missed classifications
2. **Project Adaptation**: Learn project-specific language patterns over time
3. **Confidence Calibration**: Improve confidence scoring based on user feedback
4. **Hybrid Optimization**: Optimize the threshold between pattern and AI classification

This hybrid approach provides the best balance of speed, accuracy, and cost for automatic memory classification in ADHD-optimized development workflows.