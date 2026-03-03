# ADR-105: Progressive Disclosure Pattern

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX ADHD optimization team
**Tags**: #critical #adhd #ui-pattern #cognitive-load #information-architecture

## 🎯 Context

ADHD users often experience cognitive overload when presented with too much information simultaneously. Traditional development tools frequently display all available information, options, and details at once, creating overwhelming interfaces that hinder rather than help productivity.

### ADHD Information Processing Challenges
- **Working memory limitations**: Difficulty holding multiple pieces of information simultaneously
- **Attention filtering problems**: Struggle to focus on relevant information when surrounded by details
- **Decision paralysis**: Too many options or details create overwhelming choice scenarios
- **Context switching cost**: High cognitive overhead when moving between different levels of detail
- **Cognitive fatigue**: Mental energy depleted quickly by information-dense interfaces

### Information Hierarchy Needs
Different cognitive states require different levels of information:
- **Essential information**: Must be immediately visible and actionable
- **Contextual details**: Important but secondary information available on demand
- **Technical specifics**: Detailed implementation information for deep work
- **Background information**: Reference material accessible but not prominent
- **Help and documentation**: Support information available without disruption

### Progressive Disclosure Benefits
- **Reduced cognitive load**: Only show what's needed for current task
- **Maintained focus**: Eliminate distracting secondary information
- **Flexible depth**: Allow deeper exploration without overwhelming defaults
- **Context preservation**: Maintain mental model while accessing details
- **Adaptive complexity**: Match information density to cognitive capacity

## 🎪 Decision

**DOPEMUX will implement progressive disclosure as a core UI pattern** to manage information complexity and support ADHD cognitive patterns.

### Progressive Disclosure Principles

#### 1. Essential-First Design
- **Primary action**: Most important action prominently displayed
- **Key information**: Critical details immediately visible
- **Context clues**: Just enough information to understand current state
- **Clear navigation**: Obvious path to access more details when needed

#### 2. Layered Information Architecture
```
Layer 1: Essential (Always Visible)
├── Current task or focus
├── Primary action button
├── Status indicator
└── Key context (1-2 items)

Layer 2: Contextual (One Click Away)
├── Task details and options
├── Alternative actions
├── Recent history
└── Quick settings

Layer 3: Detailed (Deliberate Access)
├── Full configuration options
├── Technical diagnostics
├── Complete history
└── Advanced features

Layer 4: Reference (Help System)
├── Documentation
├── Tutorials
├── Troubleshooting guides
└── Community resources
```

#### 3. Attention State Adaptation
```python
class ProgressiveDisclosureManager:
    def get_disclosure_level(self, attention_state: AttentionState) -> DisclosureLevel:
        if attention_state == AttentionState.SCATTERED:
            return DisclosureLevel.MINIMAL  # Essential only
        elif attention_state == AttentionState.FOCUSED:
            return DisclosureLevel.STANDARD  # Essential + context
        elif attention_state == AttentionState.HYPERFOCUS:
            return DisclosureLevel.STREAMLINED  # Task-focused
        else:  # DISTRACTED
            return DisclosureLevel.GUIDED  # Essential + guidance
```

### Implementation Patterns

#### Expandable Sections
```
🎯 Current Task: Implement authentication
   ↳ Show details ▼

[When expanded:]
🎯 Current Task: Implement authentication
├── 📋 Subtasks (3 remaining)
├── 🔗 Related files (auth.py, models.py)
├── ⏱️ Estimated time: 45 minutes
├── 📚 Relevant docs: FastAPI Auth Guide
└── Hide details ▲
```

#### Contextual Actions
```
Primary: [Continue Implementation]

Secondary actions (click for more):
├── Review requirements
├── Check tests
├── See related issues
└── Get help
```

#### Layered Help System
```
💡 Quick tip: Use --verbose for detailed output

[Want more help?]
├── 📖 Command guide
├── 🎥 Video tutorial
├── 💬 Ask community
└── 🔧 Troubleshooting
```

#### Status with Details
```
✅ Build successful (2.3s)

[Show build details ▼]
├── ✅ Linting: 0 issues
├── ✅ Tests: 47/47 passed
├── ✅ Coverage: 92%
└── 📊 Performance: +3ms vs baseline
```

### ADHD-Specific Adaptations

#### Cognitive Load Indicators
- **Information density meter**: Visual indicator of current complexity level
- **Simplify button**: One-click reduction to essential information only
- **Complexity warning**: Alert when approaching cognitive overload threshold
- **Focus mode**: Extreme simplification for scattered attention states

#### Smart Defaults
- **Learned preferences**: Remember individual information density preferences
- **Context-aware defaults**: Adjust based on current task and attention state
- **Progressive learning**: Gradually increase detail as user becomes comfortable
- **Reset options**: Easy return to simplified view when overwhelmed

#### Visual Design Elements
- **Clear hierarchy**: Typography and spacing reinforce information layers
- **Gentle transitions**: Smooth animations between disclosure levels
- **Visual breathing room**: Adequate whitespace to prevent visual overwhelm
- **Consistent patterns**: Predictable disclosure behaviors across interface

## 🔄 Consequences

### Positive
- ✅ **Reduced cognitive load**: Information presented matches cognitive capacity
- ✅ **ADHD-friendly**: Accommodates working memory and attention limitations
- ✅ **Improved focus**: Eliminates distracting secondary information
- ✅ **Flexible complexity**: Users control information depth as needed
- ✅ **Better task completion**: Simplified interface reduces task abandonment
- ✅ **Reduced overwhelm**: Prevents information overload and decision paralysis
- ✅ **Maintained context**: Progressive disclosure preserves mental model
- ✅ **Adaptive interface**: Responds to user cognitive state and preferences

### Negative
- ❌ **Hidden information**: Important details might be missed if not disclosed
- ❌ **Extra clicks**: Accessing detailed information requires additional actions
- ❌ **Design complexity**: More sophisticated interface design and implementation
- ❌ **Expert user friction**: Power users might prefer full information display
- ❌ **Discovery challenges**: Users might not know what information is available

### Neutral
- ℹ️ **Learning curve**: Users need to understand disclosure patterns
- ℹ️ **Information architecture**: Requires careful organization of information hierarchy
- ℹ️ **Testing complexity**: More interface states and transitions to validate

## 🧠 ADHD Considerations

### Working Memory Support
- **Chunked information**: Present information in manageable pieces
- **Context preservation**: Maintain mental model across disclosure levels
- **Memory aids**: Visual indicators help remember current context
- **Cognitive offloading**: System remembers details so user doesn't need to

### Attention Management
- **Focus protection**: Remove distracting secondary information
- **Selective attention**: Highlight most important information clearly
- **Attention guidance**: Visual cues direct attention to essential elements
- **Interruption recovery**: Easy return to simplified view after distractions

### Executive Function Enhancement
- **Decision simplification**: Reduce number of simultaneous choices
- **Task clarity**: Clear primary actions without option overwhelm
- **Progress visibility**: Show current state without cognitive burden
- **Goal maintenance**: Keep primary objectives visible and accessible

### Emotional Regulation
- **Overwhelm prevention**: Avoid triggering anxiety through information excess
- **Confidence building**: Success with simple interface builds user confidence
- **Stress reduction**: Simplified interface reduces cognitive stress
- **Control provision**: User controls complexity level and feels empowered

## 🔗 References
- [ADHD-Centered Design](101-adhd-centered-design.md)
- [Attention State Classification](103-attention-state-classification.md)
- [Gentle Error Handling](104-gentle-error-handling.md)
- [Gentle UX Principles](../04-explanation/adhd/gentle-ux.md)
- [Cognitive Load Management](../04-explanation/adhd/executive-function.md)
- [ADHD Optimization Hub](../04-explanation/features/adhd-optimizations.md)
- Research: ADHD working memory, progressive disclosure, and cognitive load theory