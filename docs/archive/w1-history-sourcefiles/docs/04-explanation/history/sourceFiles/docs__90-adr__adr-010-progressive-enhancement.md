# ADR-010: Progressive Enhancement Architecture for Memory Intelligence

**Status**: Proposed
**Date**: 2025-09-22
**Deciders**: Dopemux Team

## Context

The Intelligent Memory Layer introduces complex AI-powered features (classification, relationship inference, proactive surfacing) on top of the existing proven memory system. We need a strategy that:

1. **Ensures system reliability** even when new AI components fail
2. **Provides immediate value** before full AI capabilities are available
3. **Allows gradual rollout** of intelligence features
4. **Maintains ADHD-friendly experience** throughout the enhancement process

## Decision

We will implement **progressive enhancement architecture** where:

1. **Core memory system remains unchanged** - existing functionality preserved
2. **Intelligence layer adds value incrementally** - each component provides benefit independently
3. **Graceful degradation** - system works even when AI components are unavailable
4. **User-configurable intelligence levels** - developers can choose their preferred balance

## Rationale

### Reliability Through Layered Enhancement
ADHD developers depend on consistent, predictable tools. A system that sometimes works brilliantly but occasionally fails completely is worse than a system that works reliably at a basic level.

Progressive enhancement ensures:
- **Base functionality always works** (manual memory operations)
- **Each enhancement adds value** without breaking existing features
- **Failure isolation** - AI problems don't affect core memory
- **User trust maintained** through predictable behavior

### Incremental Value Delivery
Rather than requiring all intelligence features before any benefit, progressive enhancement allows:
- **Immediate deployment** with pattern-based classification
- **Gradual AI rollout** as models are trained and tested
- **Feature-by-feature enablement** based on confidence and user feedback
- **Rollback capability** if enhancements cause problems

### ADHD-Specific Considerations
Neurodivergent developers benefit from:
- **Predictable behavior** - system doesn't change unexpectedly
- **User control** - ability to disable features that don't help
- **Gentle introduction** - new features don't overwhelm
- **Fallback reliability** - always have a working baseline

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│         PROACTIVE INTELLIGENCE (Level 4)       │
│  • Contextual memory surfacing                 │
│  • Predictive relationship suggestions         │
│  • Adaptive behavior learning                  │
└─────────────────────────────────────────────────┘
                        ↓ (enhances)
┌─────────────────────────────────────────────────┐
│         RELATIONSHIP INFERENCE (Level 3)       │
│  • Automatic link discovery                    │
│  • Temporal relationship detection             │
│  • Cross-reference building                    │
└─────────────────────────────────────────────────┘
                        ↓ (enhances)
┌─────────────────────────────────────────────────┐
│         AI CLASSIFICATION (Level 2)             │
│  • LLM-powered content analysis                │
│  • Metadata extraction                         │
│  • Confidence scoring                          │
└─────────────────────────────────────────────────┘
                        ↓ (enhances)
┌─────────────────────────────────────────────────┐
│         PATTERN CLASSIFICATION (Level 1)       │
│  • Rule-based memory typing                    │
│  • Fast pattern matching                       │
│  • Context-aware routing                       │
└─────────────────────────────────────────────────┘
                        ↓ (enhances)
┌─────────────────────────────────────────────────┐
│         CORE MEMORY SYSTEM (Level 0)           │
│  • Manual memory operations (existing)         │
│  • PostgreSQL + Milvus storage                 │
│  • HTTP API endpoints                          │
└─────────────────────────────────────────────────┘
```

## Implementation Strategy

### Level 0: Core Memory (Existing - Always Available)
```python
# Existing functionality - never modified
async def mem_upsert(type: str, id: str, text: str, metadata: dict):
    """Core memory operation - always works"""
    node = MemoryNode(type=type, id=id, text=text, metadata=metadata)
    return await storage.store_node(node)
```

### Level 1: Pattern Classification (First Enhancement)
```python
class PatternEnhancement:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.fallback_to_manual = True

    async def enhanced_upsert(self, text: str, context: dict, manual_type: str = None):
        """Enhanced upsert with optional pattern classification"""

        # Always allow manual override
        if manual_type:
            return await mem_upsert(manual_type, generate_id(), text, {})

        # Try pattern classification if enabled
        if self.enabled:
            try:
                detected_type = self.pattern_classifier.classify(text, context)
                if detected_type:
                    return await mem_upsert(detected_type, generate_id(), text, context)
            except Exception as e:
                logger.warning(f"Pattern classification failed: {e}")

        # Fallback to default type
        return await mem_upsert("observation", generate_id(), text, context)
```

### Level 2: AI Classification (Second Enhancement)
```python
class AIEnhancement:
    def __init__(self, enabled: bool = False):  # Opt-in by default
        self.enabled = enabled
        self.fallback_to_patterns = True

    async def ai_enhanced_upsert(self, text: str, context: dict):
        """AI-enhanced classification with pattern fallback"""

        if not self.enabled:
            return await pattern_enhancement.enhanced_upsert(text, context)

        try:
            # Try AI classification
            ai_result = await self.ai_classifier.classify_with_metadata(text, context)
            if ai_result.confidence > 0.7:
                return await mem_upsert(
                    ai_result.type,
                    ai_result.suggested_id,
                    text,
                    ai_result.metadata
                )
        except Exception as e:
            logger.warning(f"AI classification failed: {e}")

        # Fallback to pattern classification
        return await pattern_enhancement.enhanced_upsert(text, context)
```

### Level 3: Relationship Inference (Third Enhancement)
```python
class RelationshipEnhancement:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    async def relationship_enhanced_store(self, memory: ClassifiedMemory):
        """Store memory with automatic relationship detection"""

        # Always store the core memory
        await mem_upsert(memory.type, memory.id, memory.text, memory.metadata)

        # Add relationship discovery if enabled
        if self.enabled:
            try:
                relationships = await self.relationship_inferrer.find_relationships(memory)
                for rel in relationships:
                    await graph_link(rel.from_id, rel.to_id, rel.relation, rel.metadata)
            except Exception as e:
                logger.warning(f"Relationship inference failed: {e}")
                # Memory still stored successfully, just without auto-relationships
```

### Level 4: Proactive Intelligence (Fourth Enhancement)
```python
class ProactiveEnhancement:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.user_preferences = UserPreferences()

    async def context_aware_surfacing(self, context_change: ContextChange):
        """Proactively surface relevant memories"""

        if not self.enabled or not self.user_preferences.wants_proactive_surfacing:
            return

        try:
            relevant_memories = await self.find_contextually_relevant(context_change)
            if relevant_memories and self.should_surface(context_change):
                await self.gentle_surface(relevant_memories)
        except Exception as e:
            logger.warning(f"Proactive surfacing failed: {e}")
            # Silent failure - user experience unaffected
```

## User Configuration

### Intelligence Level Settings
```yaml
# ~/.dopemux/memory-intelligence.yaml
intelligence:
  # Level 0: Core only (manual operations)
  # Level 1: + Pattern classification
  # Level 2: + AI classification
  # Level 3: + Relationship inference
  # Level 4: + Proactive surfacing
  level: 2

  # Fine-grained control
  pattern_classification: true
  ai_classification: true
  ai_model: "ollama"  # or "openai", "anthropic"
  relationship_inference: false  # opt-in
  proactive_surfacing: false     # opt-in

  # ADHD-specific settings
  gentle_enhancement: true       # Gradual feature introduction
  fallback_behavior: "graceful"  # Always degrade gracefully
  confidence_threshold: 0.7      # Only use AI when confident
```

### Progressive Onboarding
```python
class ProgressiveOnboarding:
    def __init__(self):
        self.user_comfort_level = self.assess_user_comfort()

    async def suggest_next_enhancement(self):
        """Suggest enabling next intelligence level when ready"""

        current_level = self.get_current_level()
        usage_comfort = await self.assess_usage_comfort()

        if (current_level == 1 and
            usage_comfort > 0.8 and
            self.user_has_used_for_days(7)):
            await self.gentle_suggest("Try AI classification for better accuracy?")

        elif (current_level == 2 and
              self.ai_accuracy > 0.85 and
              self.user_has_used_for_days(14)):
            await self.gentle_suggest("Enable automatic relationship detection?")
```

## Failure Handling Strategy

### Circuit Breaker Pattern
```python
class IntelligenceCircuitBreaker:
    def __init__(self):
        self.failure_count = 0
        self.last_failure = None
        self.state = "closed"  # closed, open, half-open

    async def call_with_fallback(self, intelligence_func, fallback_func, *args):
        """Call intelligence function with automatic fallback"""

        if self.state == "open":
            return await fallback_func(*args)

        try:
            result = await intelligence_func(*args)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure(e)
            return await fallback_func(*args)

    def on_failure(self, exception):
        self.failure_count += 1
        self.last_failure = datetime.now()

        if self.failure_count >= 5:
            self.state = "open"
            logger.warning("Intelligence layer disabled due to repeated failures")
```

## Benefits

### Reliability
- **Core functionality never compromised** by intelligence features
- **Predictable fallback behavior** when enhancements fail
- **User confidence maintained** through consistent base experience
- **Gradual improvement** without introducing instability

### User Experience
- **No overwhelming feature introduction** - users can adopt gradually
- **Personal control** over intelligence level
- **ADHD-friendly progression** with gentle suggestions
- **Always functional baseline** reduces anxiety about system reliability

### Development Benefits
- **Safe experimentation** with AI features
- **Independent deployment** of intelligence layers
- **Clear rollback strategy** if features cause problems
- **Measurable enhancement value** for each layer

## Risks and Mitigations

### Feature Complexity
**Risk**: Multiple intelligence levels create configuration complexity
**Mitigation**: Smart defaults, guided onboarding, simple on/off toggles

### User Confusion
**Risk**: Users don't understand which features are enabled
**Mitigation**: Clear status indicators, help documentation, diagnostic commands

### Maintenance Overhead
**Risk**: Multiple code paths increase maintenance burden
**Mitigation**: Shared interfaces, comprehensive testing, clear separation of concerns

## Consequences

### Positive
- **Reliable system evolution** without breaking existing workflows
- **User-controlled adoption** of intelligence features
- **Safe experimentation** with AI capabilities
- **ADHD-optimized enhancement** through gradual introduction

### Negative
- **Code complexity** from multiple enhancement layers
- **Configuration options** that users must understand
- **Testing complexity** across all intelligence levels
- **Documentation burden** for different feature combinations

## Alternatives Considered

### All-or-Nothing Intelligence
- **Pros**: Simpler architecture, single code path
- **Cons**: High risk of system failure, overwhelming for users
- **Rejected**: Too risky for ADHD-dependent workflows

### A/B Testing Approach
- **Pros**: Data-driven feature adoption
- **Cons**: Inconsistent user experience, harder to support
- **Rejected**: ADHD users need predictable, configurable systems

### Separate Intelligence Service
- **Pros**: Complete isolation of AI from core system
- **Cons**: Network dependency, more complex deployment
- **Future Option**: Could be considered for Level 4+ features

## Success Metrics

- **Reliability**: Core functionality maintains 99.9% uptime regardless of intelligence layer status
- **Adoption**: 80% of users advance beyond Level 1 within 30 days
- **Satisfaction**: Users report positive experience with intelligence progression
- **Fallback Effectiveness**: <5% of intelligence failures impact user workflow

This progressive enhancement architecture ensures that the Intelligent Memory Layer enhances rather than replaces the proven memory system, providing a safe and ADHD-friendly path to advanced AI capabilities.