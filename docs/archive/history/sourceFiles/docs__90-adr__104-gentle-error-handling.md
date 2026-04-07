# ADR-104: Gentle Error Handling

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX ADHD optimization team
**Tags**: #critical #adhd #error-handling #ux #gentle-ux

## 🎯 Context

Traditional error handling in development tools often creates additional stress for ADHD users through harsh language, blame-oriented messaging, and cognitive overload. Error situations already disrupt focus and increase stress; the error handling system should minimize rather than amplify these negative effects.

### ADHD Error Experience Challenges
- **Emotional dysregulation**: Harsh error messages trigger emotional responses
- **Attention disruption**: Errors break focus flow and mental model
- **Cognitive overload**: Complex error messages consume working memory
- **Shame and self-criticism**: Blame-oriented language reinforces negative self-talk
- **Decision paralysis**: Too many error recovery options create overwhelm
- **Context loss**: Traditional error handling loses development context

### Error Handling Anti-Patterns to Avoid
- **Blame language**: "You did...", "Your mistake...", "Invalid input"
- **Technical jargon**: Overwhelming users with implementation details
- **Multiple options**: Presenting too many recovery choices
- **Harsh interruptions**: Modal dialogs that completely block workflow
- **Context abandonment**: Losing work state when errors occur
- **Repetitive errors**: Same error appearing multiple times without learning

### Gentle UX Principles
- **Supportive language**: Frame errors as collaborative problem-solving
- **Context preservation**: Maintain development state during error recovery
- **Progressive disclosure**: Essential information first, details available
- **Emotional safety**: Avoid language that triggers shame or frustration
- **Clear next steps**: Specific, actionable guidance for resolution
- **Learning opportunity**: Help users understand and prevent future issues

## 🎪 Decision

**DOPEMUX will implement gentle error handling** that supports ADHD users through compassionate language, context preservation, and clear recovery guidance.

### Gentle Error Message Framework

#### Message Structure Template
```
🔧 Let's fix this together

[Brief, non-judgmental description of the situation]

💡 Here's what we can do:
[Single, clear action step]

[Optional: Brief explanation if helpful]

📚 Learn more | 🔄 Try again | ⏭️ Skip for now
```

#### Language Guidelines
- **Collaborative tone**: "Let's...", "We can...", "This happens..."
- **Supportive framing**: Focus on solutions, not blame
- **Clear communication**: Avoid technical jargon and complex explanations
- **Encouraging perspective**: Frame as normal part of development process
- **Action-oriented**: Always provide specific next steps

### Error Category Adaptations

#### Configuration Errors
```
❌ Traditional: "Invalid configuration file. Syntax error on line 45."
✅ Gentle: "🔧 I noticed something in the config that needs attention.

The YAML format in dopemux.config needs a small adjustment on line 45.

💡 I can fix this automatically, or we can look at it together.

[Fix automatically] [Show me] [Skip for now]"
```

#### Command Errors
```
❌ Traditional: "Command failed. Exit code 1. Check your syntax."
✅ Gentle: "🤔 That command didn't work as expected.

It looks like there might be a small syntax issue.

💡 Let me suggest a corrected version:
  dopemux start --session=main

[Use this] [Edit myself] [See details]"
```

#### File System Errors
```
❌ Traditional: "Permission denied. Cannot write to /path/file."
✅ Gentle: "📁 I need permission to save your work in this location.

This is a common issue we can solve together.

💡 We can either:
- Save in your user folder instead
- Fix the permissions (I'll guide you)

[Save elsewhere] [Fix permissions] [Learn more]"
```

#### Integration Errors
```
❌ Traditional: "API call failed. HTTP 401 Unauthorized."
✅ Gentle: "🔑 We need to refresh your connection to the service.

Your authentication token may have expired (this happens automatically).

💡 Let's reconnect - it takes just a moment.

[Reconnect now] [Use offline mode] [Skip this step]"
```

### Context Preservation Strategy
- **Work state protection**: Errors never cause loss of current work
- **Mental model maintenance**: Preserve user's understanding of current task
- **Session continuity**: Errors don't disrupt overall development session
- **Progress tracking**: Show that progress isn't lost due to error
- **Recovery assistance**: Help restore context after error resolution

### ADHD-Specific Error Adaptations

#### Attention State Awareness
```python
def format_error_for_attention_state(error: Error, attention_state: AttentionState) -> ErrorMessage:
    if attention_state == AttentionState.SCATTERED:
        return format_minimal_error(error)  # Essential info only
    elif attention_state == AttentionState.FOCUSED:
        return format_detailed_error(error)  # Full context and options
    elif attention_state == AttentionState.HYPERFOCUS:
        return format_quick_fix_error(error)  # Immediate solution
    else:  # DISTRACTED
        return format_gentle_redirect_error(error)  # Supportive guidance
```

#### Cognitive Load Management
- **Single action**: Present one clear next step
- **Visual clarity**: Use icons and formatting for quick scanning
- **Decision reduction**: Maximum 3 options, with recommended choice highlighted
- **Progressive detail**: Details available but not overwhelming
- **Emotional tone**: Supportive and encouraging language

## 🔄 Consequences

### Positive
- ✅ **Reduced stress**: Gentle language minimizes emotional impact of errors
- ✅ **Context preservation**: Work state maintained during error situations
- ✅ **ADHD-friendly**: Accommodates attention and emotional regulation needs
- ✅ **Learning support**: Errors become learning opportunities, not failures
- ✅ **Productivity protection**: Faster recovery and less disruption
- ✅ **Confidence building**: Supportive tone builds user confidence
- ✅ **Reduced shame**: Non-judgmental language prevents self-criticism
- ✅ **Clear guidance**: Specific next steps reduce decision paralysis

### Negative
- ❌ **Development overhead**: More complex error handling implementation
- ❌ **Message length**: Gentle messages may be longer than terse technical ones
- ❌ **Expert user friction**: Advanced users might prefer direct technical details
- ❌ **Localization complexity**: Gentle tone harder to translate accurately

### Neutral
- ℹ️ **Cultural adaptation**: Gentle approach may need cultural customization
- ℹ️ **Learning curve**: Team needs training in gentle error message writing
- ℹ️ **Maintenance overhead**: More sophisticated error message management

## 🧠 ADHD Considerations

### Emotional Regulation Support
- **Stress reduction**: Gentle language prevents error-induced emotional spikes
- **Shame mitigation**: Non-judgmental framing reduces self-criticism
- **Confidence preservation**: Supportive tone maintains user confidence
- **Emotional safety**: Error situations feel collaborative, not punitive

### Attention Protection
- **Flow preservation**: Gentle errors minimize focus disruption
- **Quick recovery**: Clear guidance enables fast return to development
- **Context maintenance**: Work state preserved through error resolution
- **Interruption minimization**: Non-intrusive error presentation

### Cognitive Load Optimization
- **Decision simplification**: Single recommended action reduces overwhelm
- **Information hierarchy**: Essential details first, complexity optional
- **Visual clarity**: Icons and formatting aid quick comprehension
- **Memory support**: Clear next steps reduce working memory burden

### Executive Function Enhancement
- **Action clarity**: Specific, concrete next steps
- **Decision support**: Recommended choices reduce decision fatigue
- **Progress preservation**: Errors don't derail overall task progress
- **Recovery scaffolding**: Structured support for error resolution

## 🔗 References
- [ADHD-Centered Design](101-adhd-centered-design.md)
- [Attention State Classification](103-attention-state-classification.md)
- [Progressive Disclosure Pattern](105-progressive-disclosure-pattern.md)
- [Gentle UX Principles](../04-explanation/adhd/gentle-ux.md)
- [Error Handling Philosophy](../94-architecture/08-concepts/error-handling.md)
- [ADHD Optimization Hub](../04-explanation/features/adhd-optimizations.md)
- Research: ADHD emotional regulation, error-induced stress, and supportive interface design