---
id: autonomous-indexing-guide
title: Autonomous Indexing Guide
type: how-to
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Autonomous Indexing Setup Guide

**Goal**: Never think about indexing again - all file changes auto-update the search index!

---

## 🎯 Current Status

**Dope-Context Index**:
- ✅ Code: 1,971 chunks indexed
- ✅ Docs: 209 chunks indexed
- ✅ Search working NOW
- ⚠️  Auto-update: Manual sync required after changes

**Serena LSP**:
- ✅ No indexing needed (real-time via LSP)
- ✅ Works immediately

---

## 🚀 Three Options for Auto-Updates

### **Option 1: MCP Autonomous Indexing** (Best - Zero-Touch)

**Status**: ✅ Code fix applied, needs MCP restart

**How to Enable**:

1. **Restart Claude Code** (picks up the `Set` import fix)

2. **Run these commands** (in Claude Code):
```python
# Enable autonomous code indexing
mcp__dope-context__start_autonomous_indexing(
    workspace_path="/Users/hue/code/dopemux-mvp",
    debounce_seconds=5.0,
    periodic_interval=600
)

# Enable autonomous docs indexing
mcp__dope-context__start_autonomous_docs_indexing(
    workspace_path="/Users/hue/code/dopemux-mvp",
    debounce_seconds=5.0,
    periodic_interval=600
)

# Verify it's running
mcp__dope-context__get_autonomous_status()
```

**Benefits**:
- ✨ Files auto-reindex 5s after save
- ✨ Periodic 10-min sync (catches missed changes)
- ✨ Zero mental overhead
- ✨ Runs inside MCP server (no extra processes)

**ADHD Impact**: 100% cognitive load reduction

---

### **Option 2: Auto-Sync Daemon** (Working NOW)

**Status**: ✅ Script created and ready

**How to Use**:

```bash
# Start background daemon (5-minute sync interval)
./scripts/auto-sync-indexing.sh start

# Check status
./scripts/auto-sync-indexing.sh status

# Watch logs
tail -f logs/auto-sync.log

# Stop
./scripts/auto-sync-indexing.sh stop
```

**How It Works**:
- Runs in background checking for changes every 5 minutes
- Only re-indexes changed files (fast!)
- Logs all activity to `logs/auto-sync.log`
- Simple PID-based process management

**Benefits**:
- ✓ Works immediately (no restart needed)
- ✓ Simple shell script
- ✓ Easy to monitor
- ⚠️  5-min delay (not instant like Option 1)

**Trade-off**: Not as instant as Option 1, but much simpler to set up

---

### **Option 3: Manual Sync** (Simplest)

**When to Use**: After making significant changes

```python
# Sync and auto-reindex changed files
mcp__dope-context__sync_workspace(
    workspace_path="/Users/hue/code/dopemux-mvp",
    auto_reindex=True
)

# Or full re-index (if needed)
mcp__dope-context__index_workspace(
    workspace_path="/Users/hue/code/dopemux-mvp"
)
```

**Benefits**:
- ✓ Complete control
- ✓ No background processes
- ✓ Works with current setup

**Trade-off**: Requires remembering to run sync

---

## 🎯 Recommended Approach

**For ADHD developers** (you!):

### **Right Now** (Immediate):
```bash
# Start the auto-sync daemon
./scripts/auto-sync-indexing.sh start

# Verify it's running
./scripts/auto-sync-indexing.sh status
```

This gives you automatic updates with 5-minute intervals.

### **Next Session** (When you restart Claude Code):
```python
# Switch to MCP autonomous indexing (instant updates)
mcp__dope-context__start_autonomous_indexing()
mcp__dope-context__start_autonomous_docs_indexing()

# Stop the shell daemon (no longer needed)
./scripts/auto-sync-indexing.sh stop
```

This upgrades to instant (5-second) updates.

---

## 🔧 Troubleshooting

### **MCP Autonomous Fails with "Set not defined"**
**Fix**: The code fix is applied. Just restart Claude Code.

**Check**:
```bash
grep "from typing import.*Set" services/dope-context/src/mcp/server.py
# Should show: from typing import Dict, List, Optional, Set, Tuple
```

### **Auto-Sync Daemon Not Detecting Changes**
**Check logs**:
```bash
tail -f logs/auto-sync.log
```

**Verify it's running**:
```bash
ps aux | grep auto-sync
./scripts/auto-sync-indexing.sh status
```

### **Search Not Finding Recent Changes**
**Force sync**:
```python
mcp__dope-context__sync_workspace(
    workspace_path="/Users/hue/code/dopemux-mvp",
    auto_reindex=True
)
```

---

## 📊 Comparison Matrix

| Feature | MCP Autonomous | Auto-Sync Daemon | Manual Sync |
|---------|----------------|------------------|-------------|
| **Update Speed** | 5 seconds | 5 minutes | On demand |
| **Setup** | Restart Claude | Run script | None needed |
| **Mental Overhead** | Zero | Very low | Low-Medium |
| **Resource Usage** | Minimal | Low | None |
| **Reliability** | High | High | Manual |
| **ADHD Optimization** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🎉 Quick Start

**Do this NOW**:

```bash
# Enable auto-sync (takes 2 seconds)
./scripts/auto-sync-indexing.sh start

# Verify
./scripts/auto-sync-indexing.sh status

# Test search
# (in Claude Code): mcp__dope-context__search_code("your query")
```

**Upgrade LATER** (after Claude restart):

```bash
# Stop shell daemon
./scripts/auto-sync-indexing.sh stop

# Enable MCP autonomous (instant updates)
# (in Claude Code): mcp__dope-context__start_autonomous_indexing()
```

---

## 💡 Summary

**Current State**:
- ✅ Search works (1,971 code + 209 docs indexed)
- ✅ Auto-sync daemon ready to use
- ✅ MCP autonomous needs Claude restart

**Recommended Flow**:
1. **NOW**: Start auto-sync daemon → 5-min updates
2. **LATER**: Restart Claude → MCP autonomous → 5-sec updates

**Best Part**: Either way, you never have to think about indexing again! 🎉
