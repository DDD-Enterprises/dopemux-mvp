# Dopemux Scripts Directory

Utility scripts for managing Dopemux services and autonomous features.

---

## 🚀 Service Management

### **start-all.sh** - Start Complete Dopemux Stack
```bash
./scripts/start-all.sh           # Start all services
./scripts/start-all.sh --verify  # Start + verify health
```

**Starts**:
- 12 MCP servers (ConPort, Zen, Serena, Context7, Exa, etc.)
- Integration Bridge (event processing, port 3016)
- Task Orchestrator (ADHD coordination, port 3014)
- All infrastructure (PostgreSQL, Redis, Qdrant)

**Equivalent to**: `dopemux mcp start-all`

---

### **stop-all.sh** - Stop All Services
```bash
./scripts/stop-all.sh
```

**Stops**: All application services (keeps infrastructure running)

---

## 🔄 Autonomous Indexing

### **simple-auto-sync.sh** - Periodic Index Updates (RECOMMENDED)
```bash
./scripts/simple-auto-sync.sh start    # Start 5-minute sync
./scripts/simple-auto-sync.sh status   # Check if running
./scripts/simple-auto-sync.sh once     # Run sync once now
./scripts/simple-auto-sync.sh stop     # Stop daemon
```

**What It Does**:
- Checks for file changes every 5 minutes
- Uses dope-context's incremental sync (SHA256-based)
- Only re-indexes changed files (fast!)
- Logs to `logs/simple-sync.log`

**ADHD Benefits**:
- ✨ Automatic updates (no manual sync needed)
- ✨ 5-minute freshness
- ✨ Zero cognitive overhead
- ✨ Works immediately (no Claude restart)

---

### **autonomous-indexing-daemon.py** - Full Autonomous (Advanced)
```bash
python scripts/autonomous-indexing-daemon.py
```

**What It Does**:
- Real-time file watching (watchdog)
- 5-second debouncing
- Instant updates

**Status**: Has import issues - use `simple-auto-sync.sh` instead for now

**Alternative**: Restart Claude Code and use MCP tools:
```python
mcp__dope-context__start_autonomous_indexing()
mcp__dope-context__start_autonomous_docs_indexing()
```

---

## 📚 Documentation

### **AUTONOMOUS_INDEXING_GUIDE.md** - Complete Setup Guide

Full guide covering:
- 3 options for auto-updates (MCP, daemon, manual)
- Step-by-step instructions
- Troubleshooting
- Comparison matrix
- Recommended approach

**Read this**: `scripts/AUTONOMOUS_INDEXING_GUIDE.md`

---

## 🎯 Quick Start

**Right Now** (no restart needed):
```bash
# Enable 5-minute auto-sync
./scripts/simple-auto-sync.sh start

# Verify it's working
./scripts/simple-auto-sync.sh status

# Check logs
tail -f logs/simple-sync.log
```

**Later** (after Claude Code restart):
```python
# Upgrade to 5-second updates
mcp__dope-context__start_autonomous_indexing()

# Stop the shell script (no longer needed)
./scripts/simple-auto-sync.sh stop
```

---

## 🔧 Utility Scripts

### **enable-autonomous-indexing.py** - Direct Python Setup
Advanced script for enabling autonomous indexing via Python.
Currently has import path issues - use MCP tools instead.

---

## 💡 Recommended Workflow

1. **Service Management**: Use `start-all.sh` / `stop-all.sh`
2. **Auto-Indexing**: Use `simple-auto-sync.sh` (works now)
3. **Upgrade Path**: MCP autonomous after Claude restart (instant updates)

---

## 📊 Feature Comparison

| Script | Purpose | Update Speed | Works Now |
|--------|---------|--------------|-----------|
| **simple-auto-sync.sh** | Periodic sync | 5 minutes | ✅ Yes |
| **MCP autonomous** | Real-time watch | 5 seconds | ⚠️  After restart |
| **Manual sync** | On-demand | Instant | ✅ Yes |

---

## 🎉 Summary

**Use THIS now**:
```bash
./scripts/simple-auto-sync.sh start
```

**Upgrade to THIS later** (after Claude restart):
```python
mcp__dope-context__start_autonomous_indexing()
```

Both handle incremental updates intelligently - only changed files get re-embedded and re-indexed!
