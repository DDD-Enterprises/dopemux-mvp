# /save: Save Dopemux Development Context

> Save your current development context including open files, mental model, cursor positions, and recent decisions for seamless restoration later.

## Overview
The `/save` command integrates with Dopemux's ADHD-optimized context manager to preserve your development session state automatically. This saves:

- **Open files** and cursor positions
- **Mental model** and current goals
- **Git state** and recent changes
- **Decisions made** during this session
- **Focus duration** and attention patterns

## Usage
```
/save [message]
```
*Examples:*
```
/save Working on memory system integration
/save Fixed the context manager bug
/save Ready to switch to testing phase
```

## How It Works
1. **Captures current state**: Files, positions, mental model, git status
2. **Generates unique session ID**: Each save creates a timestamped snapshot
3. **Stores in SQLite database**: Fast access with metadata indexing
4. **Creates JSON session file**: Detailed backup in `.dopemux/sessions/`
5. **Provides feedback**: Shows session ID and save note

## ADHD Optimizations
- **25-minute interval saves**: Automatic background preservation
- **Zero interruption**: Doesn't break your focus flow
- **Context continuity**: Seamless restoration after interruptions
- **Mental model preservation**: Recaptures your thought processes
- **Progress tracking**: Maintains focus duration across sessions

## File Locations
- **Database**: `.dopemux/context.db` (SQLite)
- **Session files**: `.dopemux/sessions/session-{id}.json`
- **Emergency saves**: `.dopemux/emergency_context.json`

## Integration with Dopemux CLI
This command works with the full Dopemux CLI:
- `dopemux save -m "message"` - Manual save
- `dopemux restore` - Restore latest session
- `dopemux status` - View session metrics

## Troubleshooting
**"No Dopemux project found"** → Run `dopemux init` first

**Save fails** → Check `.dopemux/` directory permissions

**Context not restoring** → Verify session ID with `dopemux restore --list`

## Best Practices
- **Add meaningful messages**: Helps identify session purpose later
- **Save before context switches**: Preserves mental model
- **Use with task chunks**: Save between 25-minute focus periods
- **Regular manual saves**: Supplement automatic saves

---
*Powered by Dopemux's 30-second auto-save with ADHD accommodations* 🧠