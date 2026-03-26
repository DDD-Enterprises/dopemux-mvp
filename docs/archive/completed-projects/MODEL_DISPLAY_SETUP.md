---
id: MODEL_DISPLAY_SETUP
title: Model_Display_Setup
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Model_Display_Setup (explanation) for dopemux documentation and developer
  workflows.
---
# LLM Model Display in Tmux Status Bar ✅

## Overview

The tmux status bar now displays the currently active LLM model being used by Claude Code Router. The model indicator appears between the mobile indicator and the clock.

## Display Format

| Model | Display | Color |
|-------|---------|-------|
| GPT-5-Pro | 🧠PRO | Yellow (NEON) / Purple (HOUSE) |
| GPT-5-Codex | 💻CDX | Yellow (NEON) / Purple (HOUSE) |
| GPT-5-Mini | ⚡MIN | Yellow (NEON) / Purple (HOUSE) |
| GPT-5 | 🤖GP5 | Yellow (NEON) / Purple (HOUSE) |
| Grok-4-Fast | 🚀GRK | Yellow (NEON) / Purple (HOUSE) |
| Grok-Code-Fast | ⚡GRC | Yellow (NEON) / Purple (HOUSE) |
| Grok-4-Reasoning | 🧠GRR | Yellow (NEON) / Purple (HOUSE) |
| Gemini-2-Flash | ✨GEM | Yellow (NEON) / Purple (HOUSE) |
| Llama-3.1-405B | 🦙LMA | Yellow (NEON) / Purple (HOUSE) |
| Claude-Sonnet-4.5 | 🎭CL4 | Yellow (NEON) / Purple (HOUSE) |

## How It Works

### Automatic Detection
The status bar calls `./scripts/ccr_model_tracker.sh` which:
1. Checks the CCR config for the current default model
1. Caches the result in `/tmp/dopemux_current_model.txt`
1. Returns a formatted display string

### Manual Override
You can manually set what model is displayed:

```bash
# Set specific model display
./scripts/set_model_display.sh gpt-5-pro
./scripts/set_model_display.sh gpt-5-codex
./scripts/set_model_display.sh grok-4-fast
```

### Update Frequency
- Status bar refreshes automatically based on tmux `status-interval` (default: 15 seconds)
- Cache is valid for 60 seconds
- Manual refresh: `tmux refresh-client -S`

## Status Bar Layout

```
NEON THEME:
📱 idle  🧠PRO  🕗  8:45 PM Mon Nov 04  1:orchestrator  2:agent-primary
  ^       ^       ^                       ^                ^
mobile  model   clock                  window          pane info
```

```
HOUSE THEME:
📱 idle  💻CDX  🕗  8:45 PM Mon Nov 04  1:orchestrator  2:agent-primary
  ^       ^       ^                       ^                ^
mobile  model   clock                  window          pane info
```

## Integration with CCR

The model display automatically reflects:
- **Default route**: The model set in CCR config Router.default
- **Current selection**: If you explicitly select a model in your prompt
- **Manual override**: If you use `set_model_display.sh`

## Troubleshooting

### Model not showing
```bash
# Check if script exists and is executable
ls -la scripts/ccr_model_tracker.sh

# Test the script manually
./scripts/ccr_model_tracker.sh

# Check CCR config
cat .dopemux/claude-code-router/A/.claude-code-router/config.json | jq '.Router.default'
```

### Wrong model displayed
```bash
# Clear cache
rm /tmp/dopemux_current_model.txt

# Force refresh
tmux refresh-client -S
```

### Script errors in status bar
The status bar has a fallback: if the script fails, it displays `🤖` as a generic indicator.

## Files Modified

1. `src/dopemux/tmux/cli.py` - Added model tracker to HOUSE_THEME and NEON_THEME status_right
1. `scripts/ccr_model_tracker.sh` - Model detection and formatting script (NEW)
1. `scripts/set_model_display.sh` - Manual model display setter (NEW)

## Commands

```bash
# View current model
./scripts/ccr_model_tracker.sh

# Set model display manually
./scripts/set_model_display.sh gpt-5-pro

# Clear cache
rm /tmp/dopemux_current_model.txt

# Force tmux refresh
tmux refresh-client -S
```

## Next Time You Start Tmux

When you run `dopemux start`, the status bar will automatically include the model indicator. No additional configuration needed!

---
**Completed**: 2025-11-04 04:44 UTC
