#!/bin/bash
# Manually set the current model display in tmux status bar
# Usage: ./scripts/set_model_display.sh [model-name]

MODEL="${1:-gpt-5}"
STATE_FILE="/tmp/dopemux_current_model.txt"

echo "$MODEL" > "$STATE_FILE"
echo "✅ Model display set to: $MODEL"
echo "Status bar will show: $(./scripts/ccr_model_tracker.sh)"

# Force tmux to refresh status
if command -v tmux &> /dev/null; then
    tmux refresh-client -S 2>/dev/null || true
fi
