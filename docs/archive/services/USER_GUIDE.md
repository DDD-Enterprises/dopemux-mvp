---
id: USER_GUIDE
title: User_Guide
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: User_Guide (explanation) for dopemux documentation and developer workflows.
---
# Dopemux Orchestrator TUI - User Guide

**ADHD-Optimized Multi-AI Coordination Interface**

## Quick Start (30 seconds)

```bash
# 1. Install dependencies
pip install textual textual-dev aiohttp

# 2. Launch TUI
python services/orchestrator/tui/main_with_orchestrator.py

# 3. Start commanding!
@claude what is 2+2?
```

## Core Concepts

### AI Targeting with @mentions

| Command | Effect |
|---------|--------|
| `@claude analyze auth.py` | Send to Claude only |
| `@gemini explain OAuth` | Send to Gemini only |
| `@grok review code` | Send to Grok only |
| `@all run tests` | Send to ALL available AIs in parallel |

### Visual Status Indicators

| Border Color | Meaning |
|--------------|---------|
| **Cyan** (accent) | Active pane (receives commands without @mention) |
| **Yellow** | AI is busy executing command |
| **Red** | Error occurred, check output |
| **Default** | Ready for commands |

### Keyboard Shortcuts

| Shortcut | Action | Use Case |
|----------|--------|----------|
| `Ctrl+1` | Focus Claude pane | Make Claude active target |
| `Ctrl+2` | Focus Gemini pane | Make Gemini active target |
| `Ctrl+3` | Focus Grok pane | Make Grok active target |
| `c` | Show comparison view | After `@all`, compare responses |
| `Ctrl+L` | Clear all outputs | Start fresh when panes get cluttered |
| `Ctrl+R` | Refresh energy level | Update ADHD Engine status |
| `?` | Show help | Quick reference |
| `q` | Quit | Exit TUI (with confirmation) |

## Common Workflows

### Single AI Quick Task

```
@claude what's the syntax for async/await in Python?
```

**What happens**:
1. Command appears in Claude pane with 📤 icon
2. Border turns yellow (busy)
3. Output streams in real-time as Claude responds
4. Border returns to cyan (ready) with ✅ success

**ADHD Benefit**: Visual feedback prevents "is it working?" anxiety

### Parallel Comparison

```
@all explain the difference between async and threading in Python
```

**What happens**:
1. All 3 panes show 📤 command simultaneously
2. All available CLIs execute in parallel
3. Each pane streams its AI's response independently
4. Summary shows: "📊 Parallel execution: 2.3s total | 2/3 succeeded"
5. Press `c` to see side-by-side comparison

**ADHD Benefit**: Parallel = faster results, comparison reduces decision fatigue

### Error Recovery Example

```
@gemini help with React hooks
```

**Scenario**: Gemini CLI not installed

**What happens**:
1. Pane shows: "❌ gemini CLI not available."
2. Pane shows: "   Install from: https://ai.google.dev/gemini-api/docs/cli"
3. Border turns red (error)

**ADHD Benefit**: Actionable error with clear next step

### Interrupt Recovery (Session Persistence)

**Scenario**: TUI crashes or you quit accidentally

**What happens**:
1. Auto-save runs every 30s in background
2. When you restart TUI, state restores:
   - Command history preserved
   - Last pane outputs visible
   - Progress tracking maintained
3. Visual indicator shows session age: "Session restored (15m ago)"

**ADHD Benefit**: Zero cognitive overhead for session recovery

## Advanced Features

### Retry Logic (Automatic)

When commands fail with transient errors (network timeout, rate limit), the system automatically retries with exponential backoff:

- **Attempt 1**: Immediate
- **Attempt 2**: Wait 1 second
- **Attempt 3**: Wait 2 seconds
- **Attempt 4** (final): Wait 4 seconds (max 10s)

You'll see: "⏳ Retry 1/3 in 1.0s..." in the pane

**ADHD Benefit**: Automatic recovery from temporary failures without manual intervention

### Comparison Modes

After using `@all`, press `c` to cycle through comparison modes:

1. **Side-by-Side** (default): First 5 lines from each AI
   - Quick scanning
   - See differences at a glance

2. **Sequential**: Complete outputs one after another
   - Deep analysis
   - Read each response fully

3. **Consensus**: Highlights agreements/disagreements
   - Decision-making support
   - See where AIs agree

**ADHD Benefit**: Multiple views support different cognitive modes

### Session Statistics

Check stats anytime with `?`:
- Total commands executed
- Success rate
- Average response time
- Session duration

**ADHD Benefit**: Visual progress tracking, celebrate accomplishments

## Troubleshooting

### "CLI not available" error

**Problem**: You see `❌ claude CLI not available`

**Solution**:
```bash
# Check if CLI is in PATH
which claude

# If not found, install:
npm install -g @anthropic-ai/claude-cli

# Verify installation
claude --version
```

### "Command timed out" error

**Problem**: Commands timeout after 5 minutes

**Causes**:
- Very complex prompts
- Network issues
- AI service down

**Solutions**:
1. Simplify prompt
2. Check internet connection
3. Try again later (AI service may be temporarily down)

### Outputs cluttered with old responses

**Problem**: Hard to find recent responses

**Solution**: Press `Ctrl+L` to clear all panes and start fresh

### TUI won't launch

**Problem**: `ModuleNotFoundError: No module named 'textual'`

**Solution**:
```bash
pip install textual textual-dev
```

### Session persistence not working

**Problem**: State doesn't restore after restart

**Check**:
```bash
# Is DopeconBridge running?
curl http://localhost:3016/health

# If not, start it:
cd services/mcp-dopecon-bridge
python main.py
```

**Graceful Degradation**: TUI works without ConPort, just won't persist state

## Performance Tips

### Fast Execution

- **Single AI**: Fastest for simple questions (~1-3s)
- **Parallel (@all)**: Faster than sequential for complex questions
- **Avoid timeouts**: Break complex tasks into smaller prompts

### Memory Usage

- **Output buffer**: Last 100 lines per pane (prevents memory bloat)
- **History**: Command history preserved but limited to session
- **Auto-save**: Lightweight JSON state (~10KB per save)

### Energy-Aware Usage

- **High energy** (🟢): Use complex prompts, @all commands
- **Medium energy** (🟡): Stick to single AI, simpler tasks
- **Low energy** (🔴): Take a break! System will remind you

## ADHD Optimization Features

### Visual Progress Indicators
- **Progress bar**: Shows session progress (0-100%)
- **Task counter**: "2/5 tasks ✅" provides concrete achievement
- **Break timer**: Color-coded countdown to next break
  - Green: > 10 min remaining
  - Yellow: 5-10 min
  - Red: < 5 min (take break soon!)

### Cognitive Load Reduction
- **Max 4 panes**: Prevents overwhelm
- **Color coding**: Quick status assessment without reading
- **Progressive disclosure**: Details hidden by default
- **Clear outputs**: Ctrl+L for fresh start

### Interrupt Recovery
- **Auto-save every 30s**: Never lose context
- **Session age display**: "15m ago" helps temporal awareness
- **Command history**: Resume exactly where you left off
- **Graceful errors**: Actionable messages, not cryptic codes

### Decision Reduction
- **Default target**: Claude (cyan border = active)
- **Auto-skip unavailable**: @all skips Gemini if not installed
- **Retry automatically**: Don't decide whether to retry, system handles it

## Examples

### Example 1: Quick Code Explanation
```
@claude explain this code: async def fetch(url): ...
```
**Duration**: ~2-3 seconds
**Output**: Concise explanation in Claude pane

### Example 2: Multi-AI Consensus
```
@all is microservices a good choice for a 3-person team?
```
**Duration**: ~5-8 seconds (parallel)
**Output**: All AIs respond simultaneously
**Then**: Press `c` to compare responses side-by-side

### Example 3: Code Review
```
@claude review auth.py for security issues
@gemini review auth.py for performance issues
@grok review auth.py for style issues
```
**Duration**: ~10-15 seconds
**Output**: Three different perspectives in separate panes

## Best Practices

### DO ✅
- Use `@all` for open-ended questions (multiple perspectives)
- Use specific AIs for specialized tasks (Claude for code, etc.)
- Press `c` after `@all` to see comparison
- Clear panes (Ctrl+L) when they get full
- Let retry logic handle transient failures

### DON'T ❌
- Don't manually retry failed commands (system does it)
- Don't ignore energy indicators (take breaks!)
- Don't use @all for simple factual questions (unnecessary overhead)
- Don't quit during command execution (may lose partial results)

## Version & Compatibility

**TUI Version**: Day 6 (Session Persistence)
**Tested With**:
- Claude CLI 2.0.22 ✅
- Python 3.11+ ✅
- Textual 0.40+ ✅

**Optional Dependencies**:
- DopeconBridge (port 3016) - For session persistence
- ADHD Engine - For energy level tracking

**Graceful Degradation**: TUI works without optional deps, just fewer features

## Getting Help

**In-App**: Press `?` for quick reference

**Issues**:
- Session not persisting → Check DopeconBridge running
- CLI not found → Install and add to PATH
- Timeout errors → Simplify prompts or check network

**Performance**: 0.4ms CLI detection, < 1s execution overhead

---

**Built with**: Textual Framework, asyncio, aiohttp
**Part of**: Dopemux MVP - ADHD-Optimized Development Platform
**License**: See project LICENSE file
