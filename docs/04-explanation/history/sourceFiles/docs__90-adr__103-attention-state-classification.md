# ADR-103: Attention State Classification

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX ADHD optimization team
**Tags**: #critical #adhd #attention-management #adaptive-ui

## 🎯 Context

ADHD developers experience significantly different cognitive states throughout their work sessions. The system needs to automatically detect these states and adapt its behavior to provide optimal support for each attention pattern.

### ADHD Attention State Variations
- **Focused**: Deep concentration with high cognitive capacity
- **Scattered**: Divided attention with difficulty maintaining single focus
- **Hyperfocus**: Intense concentration that may miss broader context
- **Distracted**: External or internal disruptions affecting concentration
- **Transitioning**: Moving between different attention states

### State-Dependent Needs
Each attention state requires different interface approaches:
- **Information density**: How much information can be processed effectively
- **Decision complexity**: Number of choices that can be handled
- **Interruption tolerance**: Sensitivity to notifications and changes
- **Context switching cost**: Effort required to change tasks
- **Support level**: Amount of guidance and scaffolding needed

### Classification Requirements
- **Real-time detection**: Identify state changes as they happen
- **Non-intrusive measurement**: Detect without disrupting workflow
- **High accuracy**: Correct classification to avoid inappropriate adaptations
- **Privacy protection**: Avoid invasive monitoring of personal behavior
- **Performance efficiency**: Classification must not impact system responsiveness

### Classification Approaches Considered
1. **Self-reporting**: User manually indicates current state
2. **Behavioral analysis**: Keystroke patterns, mouse movement, timing
3. **Physiological monitoring**: Heart rate, eye tracking, galvanic skin response
4. **Contextual inference**: Time of day, task complexity, recent history
5. **Hybrid approach**: Combine multiple indicators for robustness

## 🎪 Decision

**DOPEMUX will implement behavioral analysis-based attention state classification** with contextual inference and optional self-reporting override.

### Classification States

#### Focused State 🎯
**Characteristics**:
- Steady keystroke rhythm and velocity
- Minimal context switching between files
- Sustained attention on single task
- Low error rate and backspace frequency
- Consistent work patterns

**System Adaptations**:
- Full information density
- Complex technical details
- Multiple implementation options
- Advanced features available
- Minimal interruptions

#### Scattered State 🌪️
**Characteristics**:
- Irregular keystroke patterns
- Frequent file and context switching
- Higher error rate and corrections
- Short bursts of activity
- Multiple incomplete tasks

**System Adaptations**:
- Simplified information presentation
- Essential information only
- Single clear action items
- Reduced visual complexity
- Gentle guidance and focus aids

#### Hyperfocus State 🔥
**Characteristics**:
- Very high keystroke velocity
- Extended periods without breaks
- Tunnel vision on specific task
- Ignoring notifications and interruptions
- Intense concentration patterns

**System Adaptations**:
- Streamlined code generation
- Minimal explanatory text
- Direct implementation focus
- Reduced meta-commentary
- Break reminders (gentle)

#### Distracted State 😵‍💫
**Characteristics**:
- Irregular activity patterns
- Frequent pauses and hesitations
- Multiple false starts
- High correction rates
- External interruption indicators

**System Adaptations**:
- Gentle redirection
- Single, simple next steps
- Reduced cognitive demands
- Context restoration assistance
- Supportive, encouraging tone

### Classification Algorithm
```python
class AttentionStateClassifier:
    def classify_current_state(self, metrics: AttentionMetrics) -> AttentionState:
        # Behavioral indicators
        keystroke_pattern = self.analyze_keystroke_rhythm(metrics.keystrokes)
        focus_duration = self.calculate_focus_duration(metrics.activity)
        error_rate = self.calculate_error_correction_ratio(metrics.edits)
        context_switches = self.count_context_switches(metrics.file_access)

        # Contextual factors
        time_context = self.get_time_context(metrics.timestamp)
        task_complexity = self.assess_task_complexity(metrics.current_task)
        session_history = self.get_recent_state_history(metrics.session_id)

        # Classification logic
        if self.is_hyperfocus_pattern(keystroke_pattern, focus_duration, context_switches):
            return AttentionState.HYPERFOCUS
        elif self.is_focused_pattern(keystroke_pattern, focus_duration, error_rate):
            return AttentionState.FOCUSED
        elif self.is_scattered_pattern(context_switches, focus_duration, error_rate):
            return AttentionState.SCATTERED
        else:
            return AttentionState.DISTRACTED

    def get_confidence_score(self, classification: AttentionState) -> float:
        # Return confidence level (0.0-1.0) for classification accuracy
        pass
```

### Behavioral Metrics Collection
- **Keystroke analysis**: Timing, rhythm, velocity patterns
- **Mouse behavior**: Movement patterns, click frequency, hover duration
- **Application focus**: Window switching, file navigation patterns
- **Edit patterns**: Creation vs. deletion ratios, correction frequency
- **Time analysis**: Work duration, break patterns, session length

### Privacy and Ethics
- **Local processing**: All analysis happens on user's machine
- **Anonymized metrics**: No personal content analyzed, only behavioral patterns
- **Opt-out available**: Users can disable state detection
- **Transparent operation**: Clear indication when state detection is active
- **Data minimization**: Only collect metrics necessary for classification

## 🔄 Consequences

### Positive
- ✅ **Adaptive interface**: System responds appropriately to cognitive state
- ✅ **ADHD optimization**: Personalized support for different attention patterns
- ✅ **Reduced cognitive load**: Interface complexity matches cognitive capacity
- ✅ **Privacy-friendly**: Behavioral analysis without content inspection
- ✅ **Non-intrusive**: Detection happens transparently during normal work
- ✅ **Improved productivity**: Optimal support for each attention state
- ✅ **Reduced frustration**: System adapts instead of fighting user state
- ✅ **Learning enhancement**: System learns individual attention patterns

### Negative
- ❌ **Classification errors**: Incorrect state detection leads to inappropriate responses
- ❌ **Privacy concerns**: Some users uncomfortable with behavioral monitoring
- ❌ **Cold start problem**: System needs time to learn individual patterns
- ❌ **Complex implementation**: Sophisticated analysis and machine learning required
- ❌ **Resource usage**: Continuous monitoring consumes CPU and memory

### Neutral
- ℹ️ **Calibration period**: System needs time to understand individual patterns
- ℹ️ **Edge cases**: Unusual work patterns may not fit standard classifications
- ℹ️ **Cultural variations**: Attention patterns may vary across cultures and individuals

## 🧠 ADHD Considerations

### Attention State Support
- **State awareness**: Help users understand their own attention patterns
- **Predictive support**: Anticipate needs based on current state trajectory
- **Transition assistance**: Support during state changes and transitions
- **Pattern learning**: Identify individual attention rhythms and optimize timing

### Cognitive Enhancement
- **Capacity matching**: Interface complexity matches current cognitive capacity
- **Decision reduction**: Limit choices during scattered or distracted states
- **Context preservation**: Maintain mental model across attention state changes
- **Energy management**: Adapt recommendations to current cognitive energy

### Personalization Features
- **Individual calibration**: Learn unique attention patterns for each user
- **Accommodation levels**: Adjust adaptation intensity based on ADHD severity
- **Manual override**: Allow users to correct state detection when needed
- **Feedback integration**: Improve classification accuracy through user feedback

### Long-term Learning
- **Pattern recognition**: Identify personal attention rhythms and triggers
- **Optimization suggestions**: Recommend optimal times for different types of work
- **Accommodation evolution**: Adapt strategies as users develop coping mechanisms
- **Success tracking**: Monitor effectiveness of different state-based adaptations

## 🔗 References
- [ADHD-Centered Design](101-adhd-centered-design.md)
- [Auto-Save Strategy](102-auto-save-strategy.md)
- [OpenMemory Integration](506-openmemory-integration.md)
- [Attention Management Architecture](../04-explanation/adhd/attention-architecture.md)
- [ADHD Optimization Hub](../04-explanation/features/adhd-optimizations.md)
- [Progressive Disclosure Pattern](105-progressive-disclosure-pattern.md)
- Research: ADHD attention patterns, behavioral indicators, and adaptive interfaces