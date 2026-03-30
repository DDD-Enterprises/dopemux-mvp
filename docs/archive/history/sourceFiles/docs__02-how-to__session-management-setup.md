# 🧠 ADHD-Friendly Session Management Setup

This guide helps you set up the new session management slash commands (`/save`, `/restore`, `/sessions`) in Claude Code with beautiful, ADHD-optimized visual output.

## 🎯 Quick Setup

### 1. **Verify Installation**
```bash
# Test the session commands work
cd /Users/hue/code/dopemux-mvp
python scripts/test_session_integration.py
```

### 2. **Configure Claude Code MCP**
Add the session commands to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "dopemux-sessions": {
      "type": "stdio",
      "command": "python",
      "args": [
        "/Users/hue/code/dopemux-mvp/scripts/slash_commands.py",
        "{{command}}",
        "{{args}}"
      ],
      "env": {
        "PYTHONPATH": "/Users/hue/code/dopemux-mvp/src:/Users/hue/code/dopemux-mvp/scripts"
      }
    }
  }
}
```

### 3. **Test in Claude Code**
```
/save --message "Setting up session management"
/sessions
/restore --preview
```

## 🎨 Available Commands

### `/save` - Save Current Session
Save your development context with ADHD-friendly visual feedback.

```
/save                                    # Quick save with auto-description
/save --message "Working on auth system" # Save with custom message
/save --tag feature --tag python        # Save with tags
/save --force                           # Force save even if no changes
```

**Features:**
- 🎯 **Auto-descriptions** from git changes
- 🏷️  **Smart tagging** (python, feature, bugfix, docs, etc.)
- ⏰ **Time-based tags** (morning, afternoon, deep-work)
- 📊 **Visual confirmation** with session preview

### `/restore` - Restore Previous Session
Restore your development context with preview and confirmation.

```
/restore                    # Restore latest session
/restore a1b2c3d4          # Restore specific session (use first 8 chars)
/restore --preview         # Preview before restoring
```

**Features:**
- 🔍 **Session preview** before restoration
- 📁 **File restoration** with cursor positions
- 🎯 **Goal continuity** from previous session
- ✅ **Visual confirmation** of what's being restored

### `/sessions` - Browse Session Gallery
View your sessions in a beautiful, organized gallery.

```
/sessions                           # Show recent sessions
/sessions --limit 10               # Limit number of sessions
/sessions --search "feature"       # Search sessions by keyword
/sessions --tag python            # Filter by tag
```

**Features:**
- 📚 **Time-based grouping** (Today, Yesterday, This Week)
- 🎨 **Visual session cards** with emojis and progress bars
- 🔍 **Fuzzy search** through goals and messages
- 🏷️  **Tag filtering** for organization
- ⏱️ **Relative timestamps** (5 min ago, 2h ago)

### `/session-details` - Detailed Session View
Get comprehensive details about a specific session.

```
/session-details a1b2c3d4    # Show full session details
```

**Features:**
- 📊 **Complete session metadata**
- 📁 **Full file list** with paths
- 🎯 **Goals and mental model**
- 🏷️  **All associated tags**
- ⏰ **Detailed timing information**

## 🧠 ADHD-Optimized Features

### Visual Design
- **🎨 Color-coded states** - Green (success), Blue (info), Yellow (warning), Red (error)
- **📍 Emoji indicators** - Quick visual recognition without reading
- **📊 Progress bars** - Visual completion status for each session
- **⏰ Time anchoring** - "5 min ago" instead of timestamps

### Cognitive Load Reduction
- **📋 Maximum 5 items** per view to prevent overwhelm
- **🎯 Progressive disclosure** - Essential info first, details on request
- **🔍 Fuzzy search** - Find sessions without exact matching
- **🏷️  Smart tagging** - Automatic categorization reduces decisions

### Executive Function Support
- **✨ Auto-descriptions** - Smart session naming from git changes
- **📦 Session cards** - All important info in one glance
- **⏳ Focus tracking** - Shows session duration and quality
- **🔄 Context switching** - Seamless workspace transitions

## 🏷️ Smart Tagging System

### Automatic Tags
Sessions are automatically tagged based on:

**File Types:**
- `python`, `javascript`, `docs`, `config`, `testing`

**Activity Types:**
- `feature`, `bugfix`, `refactor`, `documentation`

**Work Patterns:**
- `deep-work` (45+ min), `focused` (20+ min), `quick-session` (<20 min)

**Time Context:**
- `morning`, `afternoon`, `evening`, `late-night`

**Session Status:**
- `wip`, `complete`, `checkpoint`

### Manual Tags
Add custom tags for project-specific organization:
```bash
/save --tag "sprint-3" --tag "user-auth" --tag "critical"
```

## 🎯 ADHD Workflow Patterns

### 🌊 Flow State Protection
```bash
/save --message "Deep work on auth system"    # Save before context switch
# ... handle interruption ...
/restore                                      # Quick return to flow state
```

### 🍅 Pomodoro Integration
```bash
/save --message "Pomodoro 1: API endpoints"   # Start of focused session
# ... 25 minutes of work ...
/save --tag "complete" --message "API done"   # Mark completion
# ... 5 minute break ...
/restore                                      # Continue seamlessly
```

### 🎨 Project Switching
```bash
/save --tag "project-a" --message "Pausing feature work"
# ... switch to different project ...
/sessions --tag "project-b"                   # Find project B sessions
/restore a1b2c3d4                            # Resume project B work
```

## 🔧 Troubleshooting

### Commands Not Found
1. **Check Python path**: `which python` should point to correct Python
2. **Verify modules**: `python -c "import dopemux.adhd.context_manager"`
3. **Test directly**: `python scripts/slash_commands.py save --help`

### Database Issues
```bash
# Reset session database if corrupted
rm -f .dopemux/context.db
python -c "from dopemux.adhd.context_manager import ContextManager; ContextManager('.').initialize()"
```

### Visual Display Issues
- **Rich not installed**: `pip install rich`
- **Terminal width**: Ensure terminal is at least 80 characters wide
- **Color support**: Use terminals that support ANSI colors

### Performance Issues
```bash
# Clean old sessions (older than 30 days)
python -c "
from dopemux.adhd.context_manager import ContextManager
cm = ContextManager('.')
cleaned = cm.cleanup_old_sessions(30)
print(f'Cleaned {cleaned} old sessions')
"
```

## 🎉 Success Indicators

You'll know the system is working when:

✅ **Saving sessions** shows colorful confirmation with auto-generated descriptions
✅ **Browsing sessions** displays beautiful cards grouped by time
✅ **Session search** finds sessions quickly with fuzzy matching
✅ **Restoring sessions** preserves your context and mental model
✅ **Auto-tagging** accurately categorizes your work patterns

## 🚀 Next Steps

1. **Customize tags** for your specific projects and workflows
2. **Set up regular saves** in your development routine
3. **Use session search** to track patterns and productivity
4. **Experiment with workflows** that support your ADHD needs

---

**🧠 Built for ADHD developers** - Making development accessible, one session at a time! ✨

*Need help? Check the [troubleshooting guide](./troubleshooting.md) or open an issue.*