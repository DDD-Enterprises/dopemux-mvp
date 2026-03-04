# ADR-102: Auto-Save Strategy (30-Second Interval)

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX ADHD optimization team
**Tags**: #critical #adhd #context-preservation #performance

## 🎯 Context

ADHD developers frequently experience interruptions, context switches, and attention breaks that can result in lost work and disrupted mental models. Traditional save mechanisms require explicit user action, which adds cognitive load and often fails during unexpected interruptions.

### ADHD Context Loss Challenges
- **Frequent interruptions**: External distractions, internal attention shifts, hyperfocus breaks
- **Working memory limitations**: Difficulty maintaining complex mental models during switches
- **Forgetting to save**: Cognitive overhead of remembering to preserve work
- **Context switching cost**: High penalty for losing current state during attention changes
- **Recovery time**: Significant time needed to restore mental model after interruption

### Save Strategy Requirements
- **Transparent operation**: No user intervention or cognitive load
- **Frequent preservation**: Capture state before any significant loss
- **Performance efficiency**: No impact on development workflow speed
- **Comprehensive coverage**: Save all relevant context, not just files
- **Reliable recovery**: Guaranteed restoration of previous state
- **Battery efficiency**: Minimal power consumption on laptops

### Auto-Save Interval Options
1. **Real-time (keystroke-level)**: Every change immediately saved
2. **Aggressive (5-10 seconds)**: Very frequent saves
3. **Moderate (30 seconds)**: Balanced frequency and performance
4. **Conservative (60+ seconds)**: Less frequent but lower overhead
5. **Event-driven**: Save on specific triggers (focus loss, file switch)

### Key Decision Factors
- **ADHD attention patterns**: Average interruption frequency and duration
- **System performance**: Overhead vs. development speed impact
- **Data consistency**: Avoid corruption during rapid changes
- **User experience**: Invisible operation with reliable recovery
- **Battery life**: Reasonable power consumption for mobile development

## 🎪 Decision

**DOPEMUX will implement automatic context saving every 30 seconds** with intelligent optimizations for ADHD workflow protection.

### Implementation Strategy
- **30-second base interval**: Consistent, predictable save frequency
- **Smart triggering**: Additional saves on focus loss, file changes, attention state changes
- **Background operation**: Async saves that don't block development workflow
- **Incremental saves**: Only save changed data to minimize performance impact
- **Batched operations**: Combine multiple changes into single save operation

### Context Saving Scope
```python
class ContextSaveManager:
    def auto_save_context(self):
        context = {
            "session_state": {
                "open_files": self.get_open_files(),
                "cursor_positions": self.get_cursor_positions(),
                "active_selections": self.get_selections(),
                "terminal_state": self.get_terminal_state()
            },
            "mental_model": {
                "current_task": self.get_current_task(),
                "active_thoughts": self.get_working_memory(),
                "recent_decisions": self.get_recent_decisions(),
                "next_steps": self.get_planned_actions()
            },
            "adhd_context": {
                "attention_state": self.get_attention_state(),
                "focus_duration": self.get_focus_duration(),
                "interruption_count": self.get_interruption_count(),
                "energy_level": self.estimate_energy_level()
            },
            "environment": {
                "git_state": self.get_git_status(),
                "running_processes": self.get_active_processes(),
                "environment_vars": self.get_relevant_env_vars()
            }
        }
        self.save_to_cache(context)  # Redis for speed
        self.save_to_persistent(context)  # SQLite for reliability
```

### Save Optimization Strategies
- **Change detection**: Only save when actual changes detected
- **Priority queuing**: Save critical state first, details later
- **Compression**: Compress context data to reduce I/O overhead
- **Error handling**: Graceful degradation if save fails
- **Recovery verification**: Validate save completeness

### Performance Considerations
- **Background threads**: Save operations don't block main workflow
- **I/O batching**: Combine multiple writes into single operation
- **Memory management**: Efficient data structures for context capture
- **Network efficiency**: Minimize data transfer for remote storage
- **Cache utilization**: Use Redis for immediate saves, periodic backup to disk

## 🔄 Consequences

### Positive
- ✅ **Context preservation**: Never lose more than 30 seconds of work
- ✅ **ADHD-friendly**: Automatic operation requires no cognitive overhead
- ✅ **Interruption protection**: Safe recovery from any unexpected disruption
- ✅ **Mental model continuity**: Comprehensive state capture enables full restoration
- ✅ **Performance balance**: 30-second interval provides safety without overhead
- ✅ **Reliable recovery**: Multiple save mechanisms ensure data safety
- ✅ **Attention support**: System adapts save frequency to attention patterns
- ✅ **Productivity boost**: Reduced anxiety about losing work

### Negative
- ❌ **Storage overhead**: Frequent saves consume disk space over time
- ❌ **I/O load**: Regular disk writes may impact system performance
- ❌ **Battery usage**: Additional processing may reduce laptop battery life
- ❌ **Privacy concerns**: Frequent saves might capture sensitive information
- ❌ **False confidence**: Users might rely too heavily on auto-save

### Neutral
- ℹ️ **Storage management**: Need cleanup strategy for old saves
- ℹ️ **Configuration complexity**: Tuning save frequency for different users
- ℹ️ **Debugging overhead**: More save files to manage during troubleshooting

## 🧠 ADHD Considerations

### Attention Preservation
- **Invisible operation**: Auto-save never interrupts focus flow
- **Confidence building**: Knowledge that work is safe reduces anxiety
- **Interruption recovery**: Quick restoration after attention breaks
- **Context bridging**: Comprehensive state helps recall mental model

### Cognitive Load Reduction
- **No manual saves**: Eliminates need to remember to save work
- **Stress reduction**: Lower anxiety about losing important work
- **Mental energy conservation**: Cognitive resources available for development
- **Error prevention**: Automatic safety net for forgetfulness

### ADHD-Specific Optimizations
- **Attention state awareness**: Increase save frequency during scattered attention
- **Hyperfocus protection**: Ensure saves continue during deep focus sessions
- **Transition support**: Save before predicted attention state changes
- **Recovery assistance**: Rich context enables better interruption recovery

### Adaptive Features
- **Personal patterns**: Learn individual interruption patterns
- **Context sensitivity**: Adjust save frequency based on task complexity
- **Energy awareness**: Reduce save frequency during low-energy periods
- **Smart scheduling**: Avoid saves during intensive cognitive work

## 🔗 References
- [Multi-Level Memory Architecture](003-multi-level-memory-architecture.md)
- [Cache Layer Strategy](502-cache-layer-redis.md)
- [ADHD-Centered Design](101-adhd-centered-design.md)
- [Context Preservation Theory](../04-explanation/adhd/context-theory.md)
- [Attention Management Architecture](../04-explanation/adhd/attention-architecture.md)
- [Session Management Hub](../04-explanation/features/session-management.md)
- Research: ADHD interruption patterns and working memory limitations