# Session Management - Python Project

Session persistence patterns optimized for python development with ADHD considerations.

## Session Components

### Critical State (Always Preserved)
- Working directory and active files
- Cursor positions and scroll state
- Current task and mental model
- Unsaved changes tracking

### Context-Specific State

- Virtual environment state
- Python interpreter version
- Installed packages (pip list)
- Environment variables
- Database connections
- Test runner state


### ADHD-Optimized Recovery
- Gentle re-entry prompts
- Visual progress indicators
- Time-since-last-work tracking
- Attention state restoration

## Session Triggers

### Auto-Save Events
- Every 30 seconds during active work
- Before context switches (file/directory changes)
- Before potentially disruptive operations
- On attention state changes

### Manual Save Points
- End of focused work sessions
- Before breaks or interruptions
- After completing significant milestones
- When switching between major tasks

## Recovery Patterns

### Session Restoration
```
1. Load previous session state
2. Display: "Welcome back! You were working on [task]"
3. Show: "[N] files open, last edit [time] ago"
4. Restore: File positions and cursor locations
5. Prompt: "Continue where you left off? [Y/n]"
```

### Interruption Recovery
```
1. Emergency context save on unexpected exit
2. On restart: "Session recovered from interruption"
3. Show: "Away for [duration], [changes] since you left"
4. Bridge: "You were [context], ready to continue?"
```

---

**Performance Target**: <500ms restoration time
**Storage**: Local SQLite database
**Privacy**: No sensitive data, local-only storage
