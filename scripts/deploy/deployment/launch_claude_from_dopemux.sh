#!/bin/bash
# Launch Claude Code with dopemux CCR environment
# Called from within a dopemux tmux session

# Get CCR environment from current session
CCR_API_KEY="${ANTHROPIC_API_KEY:-3-W5jDXWWaEKth9gerZogE38Mtsd_IP0ddyLFAZ-eK4}"
CCR_BASE_URL="${ANTHROPIC_BASE_URL:-http://127.0.0.1:3456}"

echo "🚀 Launching Claude Code with CCR routing..."
echo "   Base URL: $CCR_BASE_URL"
echo "   API Key: ${CCR_API_KEY:0:20}..."

# Close existing Claude
osascript -e 'quit app "Claude"' 2>/dev/null || true
sleep 1

# Launch with environment
ANTHROPIC_BASE_URL="$CCR_BASE_URL" \
ANTHROPIC_API_KEY="$CCR_API_KEY" \
open -a "Claude"

echo "✅ Claude Code launched"
