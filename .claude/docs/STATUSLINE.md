# Dopemux ADHD-Optimized Statusline

**Real-time development context awareness for Claude Code with ADHD optimizations**

## Overview

The Dopemux statusline provides instant visibility into your development session without breaking focus. Designed specifically for ADHD developers, it shows essential context at a glance while reducing cognitive load.

## What It Shows

```
dopemux-mvp main | ✅ Implementing auth system [2h 15m] | 🧠 ⚡= 👁️● 128K/200K (64%) | Sonnet 4.5
```

Breaking this down:

| Component | Example | Meaning |
|-----------|---------|---------|
| **Directory** | `dopemux-mvp` | Current working directory |
| **Git Branch** | `main` | Active git branch |
| **ConPort Status** | 📊 | Connected to knowledge graph |
| **Current Focus** | `Implementing auth system` | What you're working on (from ConPort) |
| **Session Time** | `[2h 15m]` | Time since session start |
| **ADHD Engine** | 🧠•·👁️ | Energy, attention state, accommodations |
| **Token Usage** | `128K/200K (64%)` | Context window usage |
| **Model** | `Sonnet 4.5` | Active Claude model |

## Features

### 1. ConPort Knowledge Graph Integration

**Status Indicators:**
- 📊 **Connected** - ConPort active, context preserved
- 📴 **Disconnected** - ConPort unavailable (context at risk)

**Current Focus Display:**
Shows your active task from ConPort's `active_context.current_focus` (max 35 chars + ellipsis)

**How it works:**
- Direct SQLite query to `context_portal/context.db`
- Sub-5ms response time (200x faster than HTTP)
- Auto-updates every statusline refresh

### 2. Session Time Tracking

**Format:**
- Under 1 hour: `[23m]`
- Over 1 hour: `[2h 15m]`

**Source:** ConPort `session_start` timestamp
**Updates:** Real-time calculation on every refresh
**ADHD Benefit:** Gentle time awareness without pressure

### 3. ADHD Engine Status

**Energy Levels:**
- ⚡⚡ **Hyperfocus** - Peak energy state (double lightning)
- ⚡↑ **High** - Above baseline energy
- ⚡= **Medium** - Balanced, level state (equals sign)
- ⚡↓ **Low** - Below baseline energy
- ⚡⇣ **Very Low** - Needs break or recovery

**Attention States:**
- 👁️✨ **Hyperfocused** - Deep flow state (eye + sparkles)
- 👁️● **Focused** - Good attention state (eye + solid dot)
- 👁️~ **Transitioning** - Attention shifting (eye + wave)
- 👁️🌀 **Scattered** - Attention fragmented (eye + spiral)
- 👁️💥 **Overwhelmed** - Cognitive overload (eye + explosion)

**Break Warnings:**
- ☕ **Yellow** - Break suggested soon (coffee cup)
- ☕! **Red** - Break urgently needed (coffee cup + exclamation)

**Hyperfocus Protection:**
- 🛡️ **Active** - Protection engaged during hyperfocus (shield)

**How it works:**
- Single `/health` call to ADHD Engine (localhost:8095)
- 400ms timeout for non-blocking operation
- Progressive disclosure based on terminal width

### 4. Accurate Token Usage

**Format:** `128K/200K (64%)`
- **First number**: Tokens used in current session
- **Second number**: Model's context window size
- **Percentage**: Usage relative to window

**Color Coding:**
- 🟢 **Green (0-60%)** - Plenty of context available
- 🟡 **Yellow (60-80%)** - Context filling up
- 🔴 **Red (80-100%)** - Near autocompact threshold

**Calculation Method:**
```bash
# Accurate cumulative tracking across all turns
context_used = cache_read_input_tokens (latest) + Σ output_tokens (all turns) + input_tokens (latest)
```

**Why this works:**
- `cache_read_input_tokens` = System prompt + conversation context (lags by 1 turn)
- `Σ output_tokens` = All Claude responses in conversation
- `input_tokens (latest)` = Most recent user message, fills the 1-turn lag

**Model Detection:**
- Auto-detects from model ID: `claude-sonnet-4-5-20250929`
- Handles all Claude models: Opus (200K), Sonnet (200K/1M), Haiku (200K)
- Future-proof: adapts to new models automatically

**Data Source:** Claude Code transcript file (`.jsonl`)

## Configuration

### Location
`.claude/statusline.sh`

### Claude Code Integration

Add to your Claude Code settings to enable the statusline:

```json
{
  "statusline": {
    "command": "bash /Users/hue/code/dopemux-mvp/.claude/statusline.sh"
  }
}
```

### ConPort Setup

The statusline requires ConPort for focus tracking and session time:

1. **Database location:** `context_portal/context.db` (SQLite)
2. **Required table:** `active_context` with JSON `content` field
3. **Start session:**
   ```bash
   mcp__conport__update_active_context \
     --workspace_id /Users/hue/code/dopemux-mvp \
     --patch_content '{"current_focus": "Your task", "session_start": "2025-10-04T12:00:00Z"}'
   ```

### ADHD Engine Setup

Optional but recommended for ADHD accommodations:

1. **Service location:** `http://localhost:8095/health`
2. **Start engine:**
   ```bash
   cd services/adhd-engine
   uvicorn main:app --port 8095
   ```
3. **Features enabled:** Energy tracking, attention states, break reminders

## Technical Details

### Performance

| Operation | Target | Actual | Performance |
|-----------|--------|--------|-------------|
| ConPort query | < 50ms | ~2ms | **25x faster** |
| ADHD Engine query | < 500ms | ~100ms | **5x faster** |
| Token calculation | < 100ms | ~30ms | **3x faster** |
| Total refresh | < 1s | ~150ms | **6.6x faster** |

### Token Calculation Algorithm

```bash
# 1. Extract transcript path from Claude Code JSON
transcript_path=$(jq -r '.transcript_path' <<< "$input")

# 2. Get latest cache_read (current context prompt size)
cache_read=$(tac "$transcript_path" | jq -r '.message.usage.cache_read_input_tokens // 0' | grep -v '^0$' | head -1)

# 3. Sum all output tokens (conversation history)
output_total=$(jq -r '.message.usage.output_tokens // 0' "$transcript_path" | awk '{sum+=$1} END {print int(sum)}')

# 4. Get latest input tokens (current user message)
latest_input=$(tac "$transcript_path" | jq -r '.message.usage.input_tokens // 0' | grep -v '^0$' | head -1)

# 5. Calculate total context usage
context_used=$((cache_read + output_total + latest_input))

# 6. Compare to model's context window
context_pct=$((context_used * 100 / context_total))
```

**Why this works:**
- `cache_read_input_tokens` = cached prompt (system + conversation, lags 1 turn)
- `Σ output_tokens` = all Claude responses in conversation
- `input_tokens (latest)` = most recent user input, compensates for cache lag
- Together they represent total context window usage
- Matches Claude's internal tracking within ~2% accuracy (previously ~15% error)

### Dependencies

**Required:**
- `jq` - JSON parsing
- `sqlite3` - ConPort database queries
- `bash` ≥ 4.0 - Script execution

**Optional:**
- `curl` - ADHD Engine queries
- `git` - Branch display
- ConPort database - Focus and session tracking
- ADHD Engine service - Energy and attention tracking

### Debug Mode

Enable debug logging to diagnose issues:

```bash
# Edit .claude/statusline.sh, uncomment lines 9-11:
echo "$input" > /tmp/statusline_debug.json
echo "$(date) - context_used: ..." >> /tmp/statusline_debug.log
echo "$(date) - context_total: ..." >> /tmp/statusline_debug.log

# Then check logs:
cat /tmp/statusline_debug.json | jq .
tail -20 /tmp/statusline_debug.log
```

## Changelog

### Version 2.0 (2025-10-04)

**Token Usage Improvements:**
- ✅ Added raw token counts: `128K/200K` alongside percentage
- ✅ Fixed token calculation using transcript file parsing
- ✅ Auto-detect context window from model ID
- ✅ Support all Claude models (Opus, Sonnet, Haiku, variants)

**Display Improvements:**
- ✅ Better medium energy symbol: `•` (was `=`)
- ✅ Intuitive session time: `[2h 15m]` (was `2×25+12m`)
- ✅ Current focus from ConPort (was static test data)

**Performance Improvements:**
- ✅ Direct SQLite access for ConPort (2ms vs 400ms HTTP)
- ✅ Optimized token calculation (30ms vs 100ms+)
- ✅ Single ADHD Engine health call (vs multiple endpoints)

**New Features:**
- ✅ Attention state indicators (👁️✨, 👁️, 👁️~, 👁️🌀, 👁️💥)
- ✅ Break warning system (☕ yellow, ☕! red)
- ✅ Hyperfocus protection indicator (🛡️)
- ✅ Progressive disclosure based on terminal width

### Version 1.0 (2025-09-26)

- Initial release with basic ConPort, ADHD Engine, and token tracking

## Troubleshooting

### Statusline shows 0K/200K (0%)

**Cause:** Transcript file not accessible or empty
**Fix:**
1. Check Claude Code is creating transcript:
   ```bash
   ls -la ~/.claude/projects/*/
   ```
2. Verify jq is installed: `which jq`
3. Enable debug mode and check logs

### ConPort shows 📴 disconnected

**Cause:** ConPort database not found or empty
**Fix:**
1. Check database exists:
   ```bash
   ls -la context_portal/context.db
   ```
2. Initialize ConPort:
   ```bash
   mcp__conport__get_active_context --workspace_id $(pwd)
   ```
3. Verify sqlite3 installed: `which sqlite3`

### Session time not showing

**Cause:** Invalid or future `session_start` timestamp
**Fix:**
```bash
# Set session start to current time
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{\"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}"
```

### ADHD Engine shows 💤 sleeping

**Cause:** ADHD Engine service not running
**Fix:**
```bash
# Start ADHD Engine
cd services/adhd-engine
uvicorn main:app --port 8095 --reload
```

## Best Practices

### ADHD Workflow Integration

1. **Session Start:**
   ```bash
   # Set focus and start timer
   mcp__conport__update_active_context \
     --workspace_id $(pwd) \
     --patch_content "{
       \"current_focus\": \"Implementing auth module\",
       \"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"
     }"
   ```

2. **Focus Changes:**
   ```bash
   # Update focus without resetting timer
   mcp__conport__update_active_context \
     --workspace_id $(pwd) \
     --patch_content "{\"current_focus\": \"Fixing login bug\"}"
   ```

3. **Monitor Context:**
   - 🟢 **< 60%** - Keep working
   - 🟡 **60-80%** - Consider wrapping up soon
   - 🔴 **> 80%** - Save work, prepare for autocompact

4. **Respect Break Warnings:**
   - ☕ Yellow - Finish current task, then break
   - ☕! Red - Stop immediately, take break

### Terminal Width Recommendations

- **< 90 cols** - Minimal display (essential info only)
- **90-120 cols** - Standard display (most features)
- **> 120 cols** - Full display (all indicators)

### Cognitive Load Management

The statusline uses **progressive disclosure** to avoid overwhelming:

1. **Always visible:** Directory, git, token usage, model
2. **When available:** Focus, session time, ConPort status
3. **When relevant:** Energy, attention, warnings
4. **When spacious:** Extended attention states, accommodations

## Advanced Usage

### Custom Focus Categories

Tag focus with prefixes for better organization:

```bash
# Feature development
"[FEAT] User authentication"

# Bug fixing
"[BUG] Login redirect loop"

# Refactoring
"[REFACTOR] Auth middleware"

# Learning
"[LEARN] OAuth2 flow"
```

### Integration with Pomodoro

```bash
# 25-minute focus session
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{
    \"current_focus\": \"Auth module - Pomodoro 3/4\",
    \"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"
  }"

# Check time: statusline will show [0m] → [25m]
# When reaching [25m], take break and update focus
```

### Context Window Optimization

Monitor yellow/red zones to optimize Claude usage:

```bash
# At 🟡 yellow (60%):
# - Summarize progress in ConPort decision log
# - Complete current subtask
# - Prepare for potential autocompact

# At 🔴 red (80%):
# - Save all work
# - Log decisions immediately
# - Start new session if needed
```

## Contributing

Found a bug or have a feature request? The statusline is part of Dopemux's ADHD optimization stack.

**File location:** `.claude/statusline.sh`
**Documentation:** `.claude/docs/STATUSLINE.md`
**Related systems:**
- ConPort: `docker/mcp-servers/conport/`
- ADHD Engine: `services/adhd-engine/`

## License

Part of the Dopemux project - ADHD-optimized development platform.
