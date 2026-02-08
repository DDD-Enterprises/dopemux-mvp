---
id: PROCESS_CLEANUP_GUIDE
title: Process_Cleanup_Guide
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
author: '@hu3mann'
date: '2026-02-05'
prelude: Process_Cleanup_Guide (explanation) for dopemux documentation and developer
  workflows.
---
# MCP Process Cleanup Guide

**Created**: 2025-10-16
**Issue**: Orphaned MCP processes from multiple `dopemux start` sessions causing memory leaks
**Solution**: Automatic cleanup + manual health command

## 🎯 Problems Fixed

### 1. GPT-Researcher OAuth Retry Storm (1100% CPU)
- **Container**: `dopemux-mcp-gptr-mcp`
- **Cause**: FastMCP SSE server + missing OAuth config → infinite `.well-known/oauth-*` retry loop
- **Resolution**: Container stopped (exit code 137 SIGKILL)
- **Recommendation**: Use `dopemux-gpt-researcher` instead (ADHD-optimized with proper OAuth)

### 2. Orphaned MCP Process Memory Leak
- **Cause**: `dopemux start` spawns MCP servers but never cleans them up
- **Impact**: Each session × 3 servers = exponential memory growth
- **Pattern**: ConPort + Serena + Dope-Context left running after Claude Code exits
- **Resolution**: Automatic cleanup + manual command

## ✅ Solutions Implemented

### Automatic Cleanup (Prevention)

**File**: `src/dopemux/claude/launcher.py`

**Changes**:
1. **Process Tracking**: ClaudeLauncher now tracks spawned processes and temp files
2. **Signal Handlers**: Graceful shutdown on SIGTERM/SIGINT
3. **Atexit Cleanup**: Automatic cleanup when Python exits normally

**How it works**:
```python
# On launch:
self._spawned_processes.append(claude_process)
self._temp_files.append(settings_file)

# On exit (automatic):
- Terminate Claude Code process
- Claude Code cleans up its MCP servers
- Remove temp settings files
```

### Manual Cleanup Command

**Command**: `dopemux health --cleanup`

**What it does**:
1. Scans for MCP processes (conport-mcp, serena, dope-context)
2. Checks if parent process is Claude Code
3. If parent is not Claude Code → marked as orphaned
4. Prompts to kill orphaned processes
5. Cleans up with SIGTERM

**Usage**:
```bash
# Find and kill orphaned MCP processes
dopemux health --cleanup

# Output:
# 🧹 Cleaning up orphaned MCP processes...
# Found 3 orphaned MCP processes
# Kill these processes? [Y/n]: y
# ✅ Cleaned up 3 orphaned processes
```

## 🔧 Best Practices

### Use Worktree Shell Integration (Recommended)

**Instead of multiple `dopemux start` sessions**:

```bash
# One-time setup (if not done):
dopemux shell-setup bash >> ~/.bashrc
source ~/.bashrc

# Switch worktrees with shell function (not Python):
dwt <branch-name>   # Fuzzy matching: dwt ui → matches ui-build
dwtls               # List all worktrees
dwtcur              # Show current worktree
```

**Benefits**:
- ✅ No Python process spawning
- ✅ No orphaned MCP servers
- ✅ Automatic workspace detection
- ✅ ADHD-friendly 3-letter commands
- ✅ Context preservation across switches

### Periodic Cleanup

**Add to daily workflow**:
```bash
# Check for orphans periodically
dopemux health --cleanup

# Or combine with health check:
dopemux health --cleanup --detailed
```

### Monitor Active Processes

**Watch MCP process count**:
```bash
# Count MCP processes
ps aux | grep -E "conport|serena|src.mcp.server" | grep -v grep | wc -l

# Expected:
# - 3 per active Claude Code session
# - If > (active_sessions × 3), run cleanup
```

## 🧠 ADHD Benefits

### Memory Management
- **Before**: 9-15 orphaned processes eating 500MB-1GB
- **After**: Only active sessions (3 processes per session)
- **Impact**: Reduced memory pressure, fewer context switches

### Clear Mental Model
```
1 Terminal = 1 Claude Code = 3 MCP Servers
Close Terminal → All cleaned up automatically
```

### Gentle Error Recovery
- Automatic cleanup on exit (no manual hunting)
- Manual cleanup command if things go wrong
- No scary error messages, just clean resolution

## 📊 Validation

**Current State** (2025-10-16 after fix):
```bash
$ ps aux | grep -E "conport|serena|src.mcp.server" | grep -v grep | wc -l
5

# 5 processes = 1-2 active Claude Code sessions ✅
# No orphans ✅
```

**Before Fix** (had orphans):
```bash
# 9-12 processes from 3-4 dead sessions
# Multiple dopemux start processes running
# Memory growing over time
```

## 🚨 When to Use Cleanup

### Symptoms of Orphaned Processes:
- Memory usage growing steadily
- `ps aux | grep mcp | wc -l` shows > (active_sessions × 3)
- Multiple `dopemux start` processes visible
- System feels sluggish

### Quick Check:
```bash
# How many dopemux start processes?
pgrep -f "dopemux start" | wc -l

# Should be 0-1 (only currently launching)
# If > 1, run: pkill -f "dopemux start"
```

### Full Cleanup:
```bash
# Step 1: Kill orphaned launchers
pkill -f "dopemux start"

# Step 2: Clean up orphaned MCP servers
dopemux health --cleanup

# Step 3: Verify
ps aux | grep -E "conport|serena|src.mcp.server" | grep -v grep | wc -l
# Should equal: (number of active Claude Code windows) × 3
```

## 🔄 Migration Guide

### If Using Multiple `dopemux start` Sessions

**Old workflow** (causes leaks):
```bash
# Terminal 1
cd /Users/hue/code/dopemux-mvp
dopemux start  # Spawns 3 MCP servers

# Terminal 2
cd /Users/hue/code/ui-build
dopemux start  # Spawns 3 MORE MCP servers

# Close terminals → 6 orphaned processes
```

**New workflow** (no leaks):
```bash
# Terminal 1
cd /Users/hue/code/dopemux-mvp
dopemux start  # Spawns 3 MCP servers

# Switch worktrees in SAME terminal:
dwt ui-build   # Shell function, no new processes
dwtls          # List available worktrees
dwt main       # Back to main

# Exit terminal → Automatic cleanup via atexit ✅
```

### Worktree Management Commands

```bash
# List worktrees with status
dopemux worktrees list
# OR: dwtls (after shell integration)

# Switch to worktree
dwt <branch-name>        # Fuzzy matching
dwt ui                   # Matches "ui-build"

# Show current worktree
dopemux worktrees current
# OR: dwtcur

# Clean up unused worktrees
dopemux worktrees cleanup --dry-run  # Preview
dopemux worktrees cleanup --force    # Execute
```

## 🎓 Technical Details

### Process Lifecycle

```
dopemux start
  ↓
ClaudeLauncher.__init__()
  ↓ (registers cleanup handlers)
ClaudeLauncher.launch()
  ↓ (spawns subprocess)
subprocess.Popen(["claude", "--settings", temp.json])
  ↓ (Claude Code reads settings)
Claude Code spawns MCP servers:
  - conport-mcp
  - serena v2
  - dope-context
  ↓ (User works)
User exits Claude Code
  ↓ (ClaudeLauncher cleanup triggers)
atexit.register(self._cleanup)
  ↓
process.terminate() → process.wait(5s) → process.kill()
temp_file.unlink()
  ↓
All clean! ✅
```

### Signal Handling

```python
# Registered in __init__:
signal.signal(signal.SIGTERM, self._signal_handler)
signal.signal(signal.SIGINT, self._signal_handler)

# Handler calls cleanup:
def _signal_handler(self, signum, frame):
    self._cleanup()
    sys.exit(0)
```

### Temp File Cleanup

**Pattern**: `/tmp/dopemux-claude-XXXXXXXX.json`

**Cleanup**:
- Automatic on normal exit
- Automatic on signal (SIGTERM/SIGINT)
- Manual with `dopemux health --cleanup` (for edge cases)

## 📝 Related Documentation

- **Worktree Guide**: `docs/WORKTREE_SWITCHING_GUIDE.md`
- **Shell Integration**: `dopemux shell-setup --help`
- **Health Monitoring**: `dopemux health --help`

## 🔗 Links to Decisions

- **ConPort Decision #144**: Orphaned MCP process root cause and solution
- **Related**: Two-plane architecture, ADHD session management

---

**Status**: ✅ Fully implemented and tested
**ADHD Impact**: High - eliminates memory pressure from forgotten processes
**Maintenance**: Run `dopemux health --cleanup` weekly or as needed
