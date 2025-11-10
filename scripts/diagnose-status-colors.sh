#!/bin/bash
# Diagnose status line color output issues
# Tests tmux color support and configuration

echo "🔍 Dopemux Status Line Color Diagnostics"
echo "========================================"

# Check if tmux is available
if ! command -v tmux >/dev/null 2>&1; then
    echo "❌ tmux not found. Install tmux first."
    exit 1
fi

echo "✅ tmux found: $(tmux -V)"

# Check tmux configuration
echo ""
echo "📋 Tmux Configuration Check:"
echo "----------------------------"

# Check if status bar is enabled
STATUS_ENABLED=$(tmux show-options -g status 2>/dev/null || echo "unknown")
echo "Status bar enabled: $STATUS_ENABLED"

# Check status style
STATUS_STYLE=$(tmux show-options -g status-style 2>/dev/null || echo "unknown")
echo "Status style: $STATUS_STYLE"

# Check window status styles
WINDOW_STYLE=$(tmux show-options -g window-status-style 2>/dev/null || echo "unknown")
echo "Window status style: $WINDOW_STYLE"

WINDOW_CURRENT_STYLE=$(tmux show-options -g window-status-current-style 2>/dev/null || echo "unknown")
echo "Window current style: $WINDOW_CURRENT_STYLE"

# Test color output
echo ""
echo "🎨 Color Test:"
echo "-------------"

# Test basic tmux colors
echo "Testing tmux color codes..."
echo "#[fg=colour33]Orange Text#[default] - Should be orange"
echo "#[fg=colour196]Red Text#[default] - Should be red"
echo "#[fg=colour46]Green Text#[default] - Should be green"
echo "#[fg=colour33]Tasks:#[default]0 #[fg=colour33]Dec:#[default]0 - Status line format"

# Check terminal capabilities
echo ""
echo "🖥️  Terminal Information:"
echo "-----------------------"
echo "TERM: $TERM"
echo "COLORTERM: $COLORTERM"
echo "Terminal supports colors: $(tput colors 2>/dev/null || echo "unknown")"

# Test tmux color support
echo ""
echo "🔧 Tmux Color Support Test:"
echo "---------------------------"
if tmux info 2>/dev/null | grep -q "colour"; then
    echo "✅ tmux supports color codes"
else
    echo "⚠️  tmux color support unknown"
fi

# Check for common issues
echo ""
echo "🚨 Common Issues Check:"
echo "----------------------"

# Check if status-right contains our script
STATUS_RIGHT=$(tmux show-options -g status-right 2>/dev/null || echo "none")
if echo "$STATUS_RIGHT" | grep -q "pm-status.sh"; then
    echo "✅ pm-status.sh configured in status-right"
else
    echo "⚠️  pm-status.sh not found in status-right: $STATUS_RIGHT"
fi

# Check if status-interval is reasonable
STATUS_INTERVAL=$(tmux show-options -g status-interval 2>/dev/null || echo "unknown")
if [[ "$STATUS_INTERVAL" =~ ^[0-9]+$ ]] && [ "$STATUS_INTERVAL" -gt 0 ]; then
    echo "✅ status-interval set to $STATUS_INTERVAL seconds"
else
    echo "⚠️  status-interval not properly configured: $STATUS_INTERVAL"
fi

# Test actual status line execution
echo ""
echo "🧪 Status Line Execution Test:"
echo "------------------------------"
echo "Running: ./scripts/pm-status.sh"
PM_OUTPUT="$(./scripts/pm-status.sh 2>/dev/null || echo "ERROR: Script failed")"
if [ "$PM_OUTPUT" = "ERROR: Script failed" ]; then
    echo "❌ pm-status.sh execution failed"
else
    echo "✅ pm-status.sh executed successfully"
    echo "Raw output length: ${#PM_OUTPUT} characters"
    echo "Visual output length: $(echo "$PM_OUTPUT" | sed 's/#\[[^]]*\]//g' | wc -c | tr -d ' ') characters"
fi

# Recommendations
echo ""
echo "💡 Recommendations:"
echo "-----------------"
echo "1. If colors don't show: Check your terminal color support"
echo "2. If status bar is empty: Ensure tmux status is enabled"
echo "3. If colors show as raw text: tmux color parsing may be disabled"
echo "4. Try: tmux set-option -g status on"
echo "5. Try: tmux set-option -g status-style 'bg=default,fg=default'"
echo ""
echo "Run this script inside tmux for accurate diagnostics:"
echo "tmux new-session -d -s test && tmux send-keys './scripts/diagnose-status-colors.sh' Enter && tmux attach -t test"</content>
</xai:function_call">Create diagnostic script to identify color output issues