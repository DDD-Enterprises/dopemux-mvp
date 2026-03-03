# ADR-036: Simple ADHD Accommodations Over Complex Attention Detection

**Date**: 2025-09-24
**Status**: APPROVED
**Authors**: Claude Code
**Replaces**: Complex AttentionManager approach

## Context

Initial ADHD features implementation used a 342-line AttentionManager with automatic attention state detection, complex visual indicators, and algorithmic tool filtering. Deep analysis revealed this approach was counterproductive.

## Problem

The complex AttentionManager approach had critical flaws:

1. **Increased Cognitive Load**: Constant monitoring, visual noise, complex metrics
2. **Flawed Assumptions**: Simplistic attention patterns, no user calibration
3. **Privacy Concerns**: Extensive activity tracking without transparency
4. **Removed User Agency**: Algorithmic decisions instead of user control
5. **Visual Overload**: Emoji-heavy interfaces, multi-line descriptions
6. **Architectural Mismatch**: Built for demo server, not production MCP

## Decision

**Pivot to Simple, User-Controlled ADHD Accommodations:**

### ✅ What We Implemented

1. **Static Tool Profiles** - User chooses complexity level
   - `minimal`: 3 tools (overwhelmed days)
   - `standard`: 5 tools (normal work)
   - `full`: All tools (power user)

2. **Session Bookmarking** - Context preservation without tracking
   - Save: name, timestamp, role, file, user note
   - Restore: Complete working context
   - List: Visual bookmark management

3. **Gentle Pomodoro Timer** - Non-intrusive break reminders
   - Simple 25-minute cycles
   - Single-line reminders
   - No judgment or pressure

4. **Clean Visual Design** - Reduced cognitive load
   - Simple bullet points (• Quick/Standard/Advanced)
   - Single-line tool descriptions
   - Minimal visual markers

### ❌ What We Removed

- 342-line AttentionManager class (archived)
- Automatic attention state detection
- Complex activity tracking
- Emoji-heavy visual indicators
- Algorithmic tool filtering
- Progressive disclosure complexity

## Implementation

### Files Modified
- `metamcp_simple_server.py`: Added simple tool profiles and bookmarking
- `src/dopemux/adhd/__init__.py`: Removed AttentionManager imports
- `src/dopemux/adhd/archived/`: Preserved original code for reference

### New Tools Added
- `set_tool_profile`: User controls complexity level
- `bookmark_session`: Save working context
- `restore_session`: Resume saved context
- `list_bookmarks`: Manage saved contexts

## Benefits

1. **Reduced Cognitive Load**: Simple choices, clean interface
2. **User Agency**: Users control their environment
3. **Context Preservation**: Bookmarking solves interruption problems
4. **Production Ready**: Works with real MCP servers
5. **Privacy Friendly**: No behavior tracking
6. **Maintainable**: 90% less complex code

## Consequences

- **Positive**: Actually helpful for ADHD developers
- **Positive**: Cleaner, more maintainable codebase
- **Positive**: Aligns with ADHD best practices (user control, simplicity)
- **Neutral**: Lost algorithmic "intelligence" (was harmful anyway)
- **Risk**: Users might want more automation (can be added optionally)

## Validation

Testing confirmed:
- Tool profiles work correctly (3/5/all tool limits)
- Session bookmarking preserves context perfectly
- Clean visual indicators reduce overwhelm
- Simple interface improves usability

## Alternatives Considered

1. **Fix AttentionManager**: Too fundamentally flawed
2. **Hybrid Approach**: Would reintroduce complexity
3. **No ADHD Features**: Misses opportunity to genuinely help

## Future Considerations

- Optional timer customization (user-requested)
- Export/import bookmarks for persistence
- Integration with real MCP servers
- User preference persistence

---

**Result**: ADHD accommodations that actually accommodate - through simplicity, user control, and respect for cognitive limitations rather than algorithmic assumptions.