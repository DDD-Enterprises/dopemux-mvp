# ADR-101: ADHD-Centered Design Philosophy

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX ADHD research team
**Tags**: #critical #adhd #ux #neurodivergent

## 🎯 Context

DOPEMUX is specifically designed for neurodivergent developers, particularly those with ADHD. Traditional development tools often create cognitive overhead that disrupts focus states and increases executive function demands.

### ADHD Development Challenges
- **Context switching disruption**: Breaking focus for documentation/configuration
- **Decision fatigue**: Too many options without clear guidance
- **Executive function overload**: Complex workflows requiring high cognitive planning
- **Time blindness**: Difficulty estimating task duration and break timing
- **Working memory limitations**: Losing track of complex mental models

### Research Validation
- Focus protection and executive function support identified as primary differentiators
- User testing with neurodivergent developers showed significant productivity improvements
- ADHD-optimized interfaces reduced cognitive load and stress
- Context preservation eliminated major source of focus disruption

## 🎪 Decision

**DOPEMUX will implement ADHD-centered design as a core architectural principle**, not as an accommodation layer.

### Core Design Requirements

#### 1. Flow State Preservation
- **Distraction minimization**: Batch notifications, reduce interruptions
- **Context preservation**: Automatic session state management
- **Gentle interruptions**: Non-judgmental, supportive interface language
- **Recovery support**: Easy restoration after interruptions

#### 2. Executive Function Scaffolding
- **Decision fatigue reduction**: AI-suggested defaults with clear rationale
- **Option limitation**: Maximum 3 choices presented at once
- **Clear next steps**: Always provide specific, actionable guidance
- **Progress visualization**: Clear indicators of completion and remaining work

#### 3. Timeline Support
- **ADHD-friendly task breakdown**: 25-minute focus segments
- **Early warning systems**: Proactive alerts for deadlines and dependencies
- **Flexible scheduling**: Adapt to energy levels and attention patterns
- **Break integration**: Built-in rest periods and attention recovery

#### 4. Authentic Communication
- **Supportive personality**: Encouraging, non-judgmental system responses
- **Clear explanations**: Why something is needed, not just what to do
- **Celebration**: Acknowledge completions and progress
- **Error handling**: Gentle recovery suggestions without blame

### Implementation Patterns
```
Traditional: "Error: Invalid configuration"
ADHD-Optimized: "No worries! Let's fix this config together. The issue is..."

Traditional: Complex multi-step wizard
ADHD-Optimized: One decision at a time with context preservation

Traditional: "Choose from 15 options"
ADHD-Optimized: "Here are 3 recommended options based on your project"
```

## 🔄 Consequences

### Positive
- ✅ **Improved productivity**: Reduced cognitive load enables better focus
- ✅ **Reduced stress**: Supportive interface reduces anxiety
- ✅ **Better adoption**: ADHD developers can use the tool effectively
- ✅ **Broader accessibility**: Benefits neurotypical users too
- ✅ **Competitive advantage**: Unique positioning in development tools market
- ✅ **Community building**: Attracts neurodivergent developer community

### Negative
- ❌ **Development complexity**: Requires careful UX consideration throughout
- ❌ **Additional testing**: Need neurodivergent user testing
- ❌ **Performance considerations**: Context preservation adds overhead
- ❌ **Training requirements**: Team needs ADHD awareness

### Neutral
- ℹ️ **Niche focus**: Primarily benefits neurodivergent users
- ℹ️ **Evolving understanding**: ADHD accommodation patterns still developing
- ℹ️ **User feedback dependency**: Requires ongoing neurodivergent community input

## 🧠 ADHD Design Principles

### Attention Management
- **State-aware responses**: Adapt interface based on current attention level
- **Focus protection**: Minimize context switches and interruptions
- **Recovery support**: Easy restoration after attention breaks

### Cognitive Load Reduction
- **Progressive disclosure**: Essential information first, details on request
- **Visual hierarchy**: Clear information prioritization
- **Decision support**: Reduce choice paralysis with guided options

### Executive Function Support
- **Task decomposition**: Automatic breakdown of complex work
- **Dependency tracking**: Clear prerequisites and relationships
- **Time estimation**: Realistic duration predictions with buffer time

### Memory Augmentation
- **Context preservation**: Never lose your mental model
- **Decision history**: Track choices and rationale
- **Progress tracking**: Visual indicators of completion

## 🔗 References
- [ADHD Features Hub](../04-explanation/features/adhd-optimizations.md)
- [Neurodivergent UX Requirements](../10-quality-requirements/adhd-usability.md)
- [ADHD Architecture Patterns](../08-concepts/adhd-patterns.md)
- [Executive Function Support](../04-explanation/adhd/executive-function.md)
- Research: User testing with neurodivergent developers, productivity metrics