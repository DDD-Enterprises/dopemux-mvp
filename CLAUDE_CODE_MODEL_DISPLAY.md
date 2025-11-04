# Claude Code (VS Code) Model Display ✅

## Overview

A VS Code extension that displays the current LLM model being used by Claude Code Router in the status bar.

## Installation

### Automatic (Recommended)
```bash
./scripts/install_vscode_model_display.sh
```

### Manual
Extension files are located at:
```
~/.vscode/extensions/dopemux-model-display/
├── package.json
├── extension.js
└── README.md
```

## Features

✅ **Real-time Updates** - Status bar refreshes every 5 seconds  
✅ **Auto-Detection** - Reads from CCR config automatically  
✅ **Color-Coded** - Emoji indicators for quick recognition  
✅ **Lightweight** - Minimal performance impact  
✅ **Configurable** - Adjust update interval and enable/disable

## Status Bar Location

The model indicator appears in the **bottom-right** of the VS Code status bar:

```
 Problems  Output  Debug Console  Terminal        🧠PRO  Ln 1, Col 1  UTF-8  LF
                                                    ^^^
                                               MODEL DISPLAY
```

## Model Indicators

| Model | Display | Description |
|-------|---------|-------------|
| 🧠PRO | GPT-5-Pro | Extreme thinking tasks |
| 💻CDX | GPT-5-Codex | Coding (primary fallback) |
| 🤖GP5 | GPT-5 | Default model |
| ⚡MIN | GPT-5-Mini | Quick/web search |
| 🚀GRK | Grok-4-Fast | General tasks |
| ⚡GRC | Grok-Code-Fast | Fast coding |
| 🧠GRR | Grok-4-Reasoning | Reasoning tasks |
| ✨GEM | Gemini-2-Flash | Fast responses |
| 🦙LMA | Llama-3.1-405B | Large context |
| 🎭CL4 | Claude-Sonnet-4.5 | Long context |

## Configuration

Open VS Code Settings (`Cmd+,`) and search for "Dopemux Model Display":

### Available Settings

```json
{
  "dopemuxModelDisplay.enabled": true,           // Enable/disable extension
  "dopemuxModelDisplay.updateInterval": 5000     // Update frequency (ms)
}
```

### Example: Faster Updates
```json
{
  "dopemuxModelDisplay.updateInterval": 2000     // Update every 2 seconds
}
```

### Example: Disable
```json
{
  "dopemuxModelDisplay.enabled": false
}
```

## How It Works

1. Extension activates when VS Code starts
2. Runs `scripts/ccr_model_tracker.sh` every 5 seconds
3. Falls back to reading `/tmp/dopemux_current_model.txt` if script unavailable
4. Updates status bar with formatted model display
5. Tooltip shows full model name on hover

## Usage

### Automatic Detection
The extension automatically detects the default model from your CCR config.

### Manual Override
Change what model is displayed:

```bash
# Set to GPT-5-Pro
./scripts/set_model_display.sh gpt-5-pro

# Set to GPT-5-Codex
./scripts/set_model_display.sh gpt-5-codex

# Wait ~5 seconds for status bar to update
```

### Tooltip Information
Hover over the model indicator to see:
- Full model name
- Current status
- Any error messages

## Troubleshooting

### Extension Not Showing

1. **Verify installation:**
```bash
ls -la ~/.vscode/extensions/dopemux-model-display/
```

2. **Restart VS Code:**
- Close all VS Code windows
- Reopen

3. **Check Developer Console:**
- `Help` → `Toggle Developer Tools`
- Look for any extension errors

### Wrong Model Displayed

```bash
# Clear cache
rm /tmp/dopemux_current_model.txt

# Update model
./scripts/set_model_display.sh gpt-5-pro

# Wait 5 seconds
```

### Extension Not Updating

1. Check update interval:
```json
"dopemuxModelDisplay.updateInterval": 5000  // Should be > 0
```

2. Verify tracker script works:
```bash
./scripts/ccr_model_tracker.sh
```

### Fallback Display (🤖)

If you see just `🤖`, the extension couldn't determine the model:
- CCR config might be missing
- Tracker script not found
- Permissions issue

**Fix:**
```bash
# Check CCR config
cat .dopemux/claude-code-router/A/.claude-code-router/config.json | jq '.Router.default'

# Manually set model
./scripts/set_model_display.sh gpt-5
```

## Files

### Extension Files
- `~/.vscode/extensions/dopemux-model-display/package.json` - Extension manifest
- `~/.vscode/extensions/dopemux-model-display/extension.js` - Main logic
- `~/.vscode/extensions/dopemux-model-display/README.md` - Extension docs

### Supporting Scripts
- `scripts/ccr_model_tracker.sh` - Model detection script
- `scripts/set_model_display.sh` - Manual model setter
- `scripts/install_vscode_model_display.sh` - Installation script

## Activation & Restart

After installation or changes:
1. **Quit VS Code completely** (`Cmd+Q`)
2. **Reopen VS Code**
3. Look for model indicator in bottom-right status bar
4. Wait ~5 seconds for first update

## Integration with Claude Code Router

The extension integrates seamlessly with CCR:
- Shows **default route** from CCR config
- Updates when you **manually override** the model
- Reflects **route changes** (think, background, etc.)
- Works with **all configured models**

## Performance

- **Lightweight**: < 1MB total
- **Low CPU**: Updates only every 5 seconds
- **No network**: Reads local files only
- **Fast startup**: Activates in < 100ms

## Uninstallation

```bash
rm -rf ~/.vscode/extensions/dopemux-model-display
```

Then restart VS Code.

---
**Created**: 2025-11-04 04:48 UTC  
**Version**: 1.0.0
