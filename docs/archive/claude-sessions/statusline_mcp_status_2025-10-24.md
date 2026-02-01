---
id: statusline_mcp_status_2025-10-24
title: Statusline_Mcp_Status_2025 10 24
type: historical
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# Statusline MCP Server Status Indicators

**Date**: 2025-10-24
**Feature**: At-a-glance MCP server health monitoring

## What Was Added

### Visual MCP Server Status

The statusline now shows the status of 6 core MCP servers:

```
dopemux-mvp main | ✅ Focus [2h] | 📚🧠🔬📊🔎🖥️ | 💤 215K/1000K (21%) | Sonnet
                                    ^^^^^^^^^^^^
                                    MCP Status (6 servers)
```

**Indicator Meanings**:
- **📚** (Book) - Context7 (Documentation) - Port 3002
- **🧠** (Brain) - Zen (Multi-model reasoning) - Port 3003
- **🔬** (Microscope) - Serena (Code intelligence) - Port 3006
- **📊** (Chart) - DDG-MCP (Decision Graph) - Port 3016
- **🔎** (Magnifier right) - Dope-Context (Semantic Search via Qdrant) - Port 6333
- **🖥️** (Desktop) - Desktop-Commander (Context switching) - Port 3012

**Status**:
- **Icon visible** = Server is UP ✅
- **⚠️** (Warning) = Server is DOWN ❌

### Examples

**All servers up**:
```
| 📚🧠🔬📊🔎🖥️ |
```

**Zen is down**:
```
| 📚⚠️🔬📊🔎🖥️ |
```

**DDG and Dope-Context down**:
```
| 📚🧠🔬⚠️⚠️🖥️ |
```

## Why These 6 Servers?

These are the **core MCP servers** for ADHD-optimized development:

1. **Context7 📚** - Official documentation lookup (prevents guessing APIs)
2. **Zen 🧠** - Multi-model reasoning (thinkdeep, consensus, debug, planner)
3. **Serena 🔬** - Code intelligence (LSP navigation, complexity scoring)
4. **DDG-MCP 📊** - Decision graph queries (related decisions, instance diff, cross-workspace)
5. **Dope-Context 🔎** - Semantic code/docs search (AST-aware, ADHD-optimized)
6. **Desktop-Commander 🖥️** - Context switch recovery (ADHD critical)

**Not shown** (managed differently):
- ConPort - Has dedicated ✅/⚠️ indicator (already in statusline)
- ADHD Engine - Has 🧠/💤 indicator + energy/attention symbols
- Dope-Context - Stdio MCP (no HTTP port)
- Exa, GPT-Researcher - Supporting services (not critical path)

## Implementation Details

### Port Checks

Uses `nc -z` (netcat zero I/O mode) for fast port availability checks:

```bash
if nc -z localhost 3002 2>/dev/null; then MCP_CONTEXT7="📚"; fi
if nc -z localhost 3003 2>/dev/null; then MCP_ZEN="🧠"; fi
if nc -z localhost 3006 2>/dev/null; then MCP_SERENA="🔬"; fi
if nc -z localhost 3016 2>/dev/null; then MCP_DDG="📊"; fi
if nc -z localhost 6333 2>/dev/null; then MCP_DOPE="🔎"; fi
if nc -z localhost 3012 2>/dev/null; then MCP_DESKTOP="🖥️"; fi
```

**Special Cases**:
- **Dope-Context 🔎**: Stdio MCP (no HTTP server). Checks Qdrant port 6333 as critical dependency.
- **DDG-MCP 📊**: HTTP bridge for decision graph queries across worktrees.

**Why nc instead of curl?**
- ⚡ **Faster**: <5ms vs 50-200ms per check
- 💡 **Simpler**: Just checks if port is listening
- 🎯 **Sufficient**: Don't need full HTTP health check for statusline

### Performance

- **Check time**: ~30ms total (6 servers sequentially, but nc is blazing fast)
- **Overhead**: Negligible (statusline updates every keystroke)
- **No timeout needed**: nc is instant if port is closed

**Note**: Sequential checks are fine since nc is so fast (~5ms each). Parallel backgrounding would add complexity for minimal gain.

## ADHD Benefits

### At-a-Glance Awareness
- See MCP server health without running commands
- No context switch to check `docker ps`
- No mental load remembering which servers are critical

### Proactive Problem Detection
- Spot missing servers BEFORE trying to use them
- Red ⚠️ draws attention immediately
- Prevents "why isn't X working?" debugging cycles

### Reduced Interruptions
- Don't discover broken servers mid-workflow
- Can start servers preemptively if down
- Maintains flow state

## Troubleshooting

### All Servers Show ⚠️

**Cause**: MCP servers aren't running

**Fix**:
```bash
dopemux mcp start-all
```

### Specific Server Shows ⚠️

**Check if container is running**:
```bash
docker ps --filter "name=mcp-context7"  # Replace with server name
```

**Check container logs**:
```bash
docker logs mcp-context7
```

**Restart specific server**:
```bash
cd docker/mcp-servers
docker-compose restart context7
```

### nc: command not found

**Cause**: netcat not installed (rare on macOS/Linux)

**Fix**:
```bash
# macOS
brew install netcat

# Ubuntu/Debian
sudo apt-get install netcat
```

**Fallback**: Statusline will show ⚠️ for all servers (safe failure)

## Files Modified

- `.claude/statusline.sh` - Lines 160-170 (MCP checks), 262-264 (display)

## Related Features

- ConPort status: ✅/⚠️ (SQLite query, no HTTP)
- ADHD Engine: 🧠/💤 (HTTP health check with full state)
- Session time: [2h 15m] (from ConPort active_context)
- Context usage: 215K/1000K (21%) (from transcript parsing)

## Future Enhancements

Potential additions (not implemented):
- Click-to-restart functionality (if terminal supports)
- Color coding (green/red) instead of emoji swap
- Show latency or response time
- Tooltip with service version on hover
