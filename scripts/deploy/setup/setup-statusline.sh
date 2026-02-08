#!/bin/bash
# Dopemux Statusline Setup Script
# Configure tmux and Claude Code statuslines with improved context-aware display

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🧠 Dopemux Statusline Setup"
echo "============================"

# Check if tmux is available
if ! command -v tmux >/dev/null 2>&1; then
    echo "❌ tmux not found. Please install tmux first."
    exit 1
fi

# Check if pm-status.sh exists
if [ ! -f "$SCRIPT_DIR/pm-status.sh" ]; then
    echo "❌ pm-status.sh not found in scripts directory"
    exit 1
fi

echo "✅ Found required components"

# Test pm-status.sh
echo ""
echo "Testing pm-status.sh..."
PM_OUTPUT="$("$SCRIPT_DIR/pm-status.sh" 2>/dev/null || echo "ERROR")"
if [ "$PM_OUTPUT" = "ERROR" ]; then
    echo "⚠️  pm-status.sh returned error, but continuing setup"
else
    echo "✅ pm-status.sh working: $PM_OUTPUT"
fi

# Create tmux configuration snippet
echo ""
echo "Creating tmux configuration..."

TMUX_CONFIG="$HOME/.tmux.dopemux.conf"

cat > "$TMUX_CONFIG" << 'EOF'
# Dopemux ADHD-Optimized Tmux Configuration
# Add this to your ~/.tmux.conf: source-file ~/.tmux.dopemux.conf

# Status bar styling
set -g status-style "bg=colour0,fg=colour7"
set -g status-left "#[fg=colour33]#[bg=colour0] 🧠 Dopemux PM #[default]"
set -g status-right "#[fg=colour166]#[bg=colour0] #(export TMUX_WIDTH_LIMIT=120; /path/to/dopemux/scripts/pm-status.sh) #[default]"

# Window styling
set -g window-status-current-style "bg=colour33,fg=colour0,bold"
set -g window-status-style "bg=colour0,fg=colour244"

# Status bar updates every 15 seconds
set -g status-interval 15

# Enable status bar
set -g status on
EOF

# Replace the path in the config
sed -i.bak "s|/path/to/dopemux|$PROJECT_ROOT|g" "$TMUX_CONFIG"

echo "✅ Created $TMUX_CONFIG"
echo ""
echo "To enable Dopemux statusline in tmux:"
echo "1. Add this line to your ~/.tmux.conf:"
echo "   source-file $TMUX_CONFIG"
echo ""
echo "2. Reload tmux configuration:"
echo "   tmux source ~/.tmux.conf"
echo ""
echo "3. Or apply to current session:"
echo "   tmux source-file $TMUX_CONFIG"

# Check if Claude Code statusline is configured
CLAUDE_STATUSLINE="$PROJECT_ROOT/.claude/statusline.sh"
if [ -f "$CLAUDE_STATUSLINE" ]; then
    echo ""
    echo "✅ Claude Code statusline already configured at $CLAUDE_STATUSLINE"
    echo "The statusline will automatically use the improved pm-status.sh integration"
else
    echo ""
    echo "ℹ️  Claude Code statusline not found. Make sure you're in the project root when using Claude Code."
fi

echo ""
echo "🎉 Setup complete! Your tmux statusline now includes:"
echo "   - Context-aware PM metrics (tasks, decisions, blockers)"
echo "   - MCP server status icons"
echo "   - ADHD Engine state (energy, attention, cognitive load)"
echo "   - Crisis mode for urgent issues"
echo "   - Progressive disclosure based on available space"
echo ""
echo "Environment variables you can set:"
echo "   TMUX_WIDTH_LIMIT=100    # Override default width limit"
echo "   CONTEXT_AWARE_PRIORITY=true  # Enable context-aware display"
