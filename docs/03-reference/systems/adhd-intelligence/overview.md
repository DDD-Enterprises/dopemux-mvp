---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Readme (reference) for dopemux documentation and developer workflows.
---
# ADHD Intelligence System (Serena)

The ADHD Intelligence System, powered by Serena AI, provides cognitive support, break management, and productivity optimization specifically designed for ADHD developers.

## Quick Links

- **[ADHD Complete Documentation](adhd-complete-documentation.md)** - Comprehensive system guide
- **[ADHD Stack README](adhd-stack-readme.md)** - Technology stack overview
- **[Architecture Diagram](../../../04-explanation/architecture/adhd-architecture-diagram.md)** - Visual system architecture

## Overview

Serena is Dopemux's ADHD intelligence engine that:
- **Monitors cognitive state** - Energy levels, focus duration, context switching
- **Suggests intelligent breaks** - Based on patterns, not arbitrary timers
- **Prevents burnout** - Detects fatigue patterns early
- **Optimizes flow** - Minimizes interruptions during deep work
- **Learns patterns** - Adapts to your unique work style

## Documentation Index

### Complete Documentation
- [ADHD Complete Documentation](adhd-complete-documentation.md) - Everything about the system
- [ADHD Stack README](adhd-stack-readme.md) - Tech stack and components

### Architecture & Design
- [Architecture Diagram](../../../04-explanation/architecture/adhd-architecture-diagram.md) - Visual overview
- [ADHD Engine Deep Dive](adhd-engine-deep-dive.md) - Core concepts, pattern detection, and break strategy
- [Serena V2 Quick Test](serena-v2-quick-test.md) - Runtime verification guide

### Component Documentation
See [04-explanation/](../../../04-explanation/) for:
- Component 6: ADHD Intelligence
- Component 6: Phase 2 Specification
- Component 6: Phase 3 Specification
- Component 7: Environmental Interruption Shield

## Core Features

### 1. Cognitive State Tracking
Monitors:
- Current energy level (1-10)
- Focus duration (time in flow state)
- Context switches (interruption frequency)
- Break history and effectiveness

### 2. Intelligent Break Suggestions
Based on:
- Time since last break
- Current energy level
- Task complexity
- Historical patterns
- Environmental factors

### 3. Pattern Learning
Learns:
- Your productive hours
- Optimal break timing
- Energy fluctuation patterns
- Task-specific focus needs

### 4. Interruption Shield
Protects:
- Deep work sessions
- Flow state periods
- Critical task completion
- Energy-intensive work

## Integration Points

### Dashboard
Displays:
- Current cognitive state
- Break recommendations
- Energy level indicators
- Pattern insights

### ConPort
Tracks:
- Session productivity metrics
- Context quality scores
- Break effectiveness
- Pattern data for learning

### Task Orchestrator
Influences:
- Task scheduling based on energy
- Break insertion timing
- Context switch management
- Work session planning

## Usage

### Basic Monitoring
Serena runs automatically and tracks:
- Session duration
- Break timing
- Energy indicators
- Focus metrics

### Break Suggestions
When Serena suggests a break:
1. **Yellow indicator** - Consider a break soon
1. **Orange indicator** - Break recommended
1. **Red indicator** - Break strongly recommended

### Customization
Configure in profile YAML:
```yaml
adhd_settings:
  energy_tracking: true
  break_reminders: true
  min_break_interval: 25  # minutes
  max_work_duration: 90   # minutes
  interruption_shield: true
```

## Metrics & Insights

### Tracked Metrics
- Energy level over time
- Break frequency and duration
- Context switch rate
- Flow state duration
- Productivity patterns

### Insights Provided
- Optimal work/break ratios
- Best productive hours
- Energy patterns by task type
- Burnout risk indicators
- Recovery recommendations

## Development Status

✅ **Core Engine**: Production-ready
✅ **Pattern Learning**: Active
✅ **Dashboard Integration**: Complete
🚧 **Advanced Predictions**: In development
🚧 **Mobile Companion**: Planned

## Related Documentation

### In This Repository
- [Architecture](../../../04-explanation/architecture/)
- [Component Specs](../../../04-explanation/)
- [API Reference](../../)
- [How-To Guides](../../../02-how-to/)

### External Resources
- ADHD research papers (see bibliography in docs)
- Flow state optimization studies
- Cognitive load management research

## Troubleshooting

### Break suggestions not appearing
- Check ADHD settings in profile
- Verify Serena service is running
- Review dashboard configuration

### Metrics not tracking
- Confirm PostgreSQL connection
- Check session initialization
- Verify ConPort integration

### Pattern learning not adapting
- Ensure minimum data collection (1 week)
- Check pattern analysis service
- Review logged metrics

## Contributing

When working on ADHD intelligence:
1. Review deep dive documentation first
1. Understand cognitive science principles
1. Test with real ADHD developers
1. Validate against research
1. Document new patterns discovered

---

**Maintained by:** ADHD Intelligence Team
**Last Updated:** 2025-10-29
**Status:** Production-ready with ongoing enhancements
