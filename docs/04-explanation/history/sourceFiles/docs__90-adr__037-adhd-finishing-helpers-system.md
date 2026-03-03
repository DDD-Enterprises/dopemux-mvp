# ADR-037: ADHD Finishing Helpers System

**Status**: Accepted
**Date**: 2025-09-25
**Context**: ADHD developers struggle with project completion - "finishing is harder than starting"

## Context

ADHD developers face unique challenges completing projects once they reach 80-90% completion:

- **"There is NOW and NEVER"** - Time blindness creates urgency distortion
- **"Out of sight = out of mind"** - Almost-finished work becomes invisible after context switches
- **Dopamine crashes near completion** - The hardest part is crossing the finish line
- **Context switching kills momentum** - Losing "finishing state" when interrupted
- **Executive dysfunction** - Need external structure for completion workflows

User feedback explicitly rejected "half-baked implementations" and requested systems that genuinely help with finishing rather than starting projects.

## Decision

Implement **ADHD Finishing Helpers System** as **Core Dopemux Integration** rather than external tooling.

### Architecture Choice: Core Integration

**Selected over**:
- Enhanced MCP tooling (lacks persistence, fails "out of sight = out of mind")
- Hybrid approach (over-engineering, too much complexity)

**Rationale**:
- Leverages existing SessionManager with sophisticated ADHD accommodations
- Provides guaranteed persistence across container restarts and session interruptions
- Natural integration with git worktree system and session save/restore
- Addresses core ADHD requirement: "almost-done work stays visible across sessions"

### Key Components

1. **In-Progress Work Tracking**
   - Dynamic list shown on Claude startup via slash command
   - Manual add/update/remove capabilities
   - Persistent across all session interruptions
   - Integration with existing Dopemux workflows

2. **Completion Detection Engine**
   - Extends existing SessionMetrics with completion percentage
   - Git-aware progress detection (branch state, test coverage, documentation)
   - Smart "almost done" threshold detection (80-95% completion)

3. **ADHD-Optimized Visual System**
   - Progressive intensity: gentle → active → urgent as completion approaches
   - Terminal integration with existing Dopemux status displays
   - Celebration/reward system for dopamine reinforcement
   - Zero additional cognitive load (automatic workflow integration)

4. **Persistent Context Preservation**
   - Extends existing ContextSnapshot with completion state
   - Survives container restarts, session switches, interruptions
   - Integration with Letta memory system for long-term context

## Implementation Strategy

### Phase 1: Foundation (Weeks 1-3)
- Extend SessionManager and ContextSnapshot for completion tracking
- Implement basic `dopemux status --completion` functionality
- Add git state analysis for project progress detection
- Validate performance impact and data persistence

### Phase 2: ADHD Visual System (Weeks 4-6)
- Terminal status integration with progress indicators
- Session restore with completion context awareness
- User-configurable visual intensity and celebration systems
- ADHD user testing and feedback integration

### Phase 3: Advanced Intelligence (Ongoing)
- Smart completion signal detection (tests, docs, code quality)
- Integration with task management systems
- Pattern recognition for personalized completion assistance

## Consequences

### Positive
- Addresses real ADHD completion challenges with proven architecture
- Leverages existing sophisticated SessionManager system
- Persistent visibility ensures "almost done" work never disappears
- Natural workflow integration reduces cognitive load
- Phased approach allows validation and course correction

### Negative
- More complex than external tooling approach
- Requires deep integration with Dopemux core systems
- Higher initial development investment
- Need ADHD user validation for effectiveness

### Risks & Mitigations
- **Integration Complexity**: Start with minimal viable integration, validate early
- **Performance Impact**: Implement lazy loading and caching for completion calculations
- **User Overwhelm**: Begin with single progress indicator, add complexity gradually
- **Abandonment Risk**: Ensure immediate value even with minimal features

## Success Metrics

### Technical Success
- Zero measurable performance impact on existing `dopemux` commands
- 100% data persistence across session restarts
- Git state detection accuracy >90% for standard project patterns

### ADHD User Success
- Positive feedback from ADHD beta testers on completion awareness
- Measurable reduction in context switching away from >80% complete projects
- User adoption of completion celebration features
- Increased project completion rates in 90%+ range

### Integration Success
- Natural workflow integration without additional cognitive steps
- Seamless coordination with existing session management
- Enhanced rather than disrupted development experience

## Related Decisions
- ADR-036: ADHD Simple Accommodations (foundation for this system)
- ADR-101: ADHD-Centered Design (design principles applied here)

## Implementation Notes
- Builds on existing `src/dopemux/mcp/session_manager.py` architecture
- Extends `SessionMetrics` and `ContextSnapshot` classes
- Coordinates with `src/dopemux/adhd/context_manager.py` for persistence
- Integration points documented in `/docs/02-how-to/finishing-helpers-implementation.md`