#!/bin/bash
# 🚀 DOPE Layout - Complete Launch & Enhancement Script
# Run this to get the FULL experience!

set -e

echo "╔════════════════════════════════════════╗"
echo "║   🚀 DOPE LAYOUT - FULL SETUP 🚀      ║"
echo "╚════════════════════════════════════════╝"
echo

# Step 1: Launch DOPE layout
echo "📍 Step 1: Launching DOPE layout..."
echo "─────────────────────────────────────────"

if tmux has-session -t dopemux 2>/dev/null; then
    echo "⚠️  Existing dopemux session found"
    read -p "Kill and restart? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        tmux kill-session -t dopemux
        echo "✅ Killed existing session"
    else
        echo "ℹ️  Using existing session"
    fi
fi

if ! tmux has-session -t dopemux 2>/dev/null; then
    echo "🎨 Starting new DOPE session..."
    cd "$(dirname "$0")"
    python3 -m dopemux.cli tmux start --layout dope 2>&1 | grep -v "^$" || true
    sleep 2
    echo "✅ DOPE layout started"
fi

echo

# Step 2: Apply enhancements
echo "📍 Step 2: Applying enhancements..."
echo "─────────────────────────────────────────"

if [ -f scripts/enhance_dope_layout.sh ]; then
    bash scripts/enhance_dope_layout.sh dopemux
else
    echo "⚠️  Enhancement script not found, skipping"
fi

echo

# Step 3: Show what's available
echo "📍 Step 3: Your DOPE Layout is ready!"
echo "─────────────────────────────────────────"
echo
echo "🎯 What you have:"
echo "  ✅ Bigger orchestrator pane (75% width, 55% height)"
echo "  ✅ Taller agent panes (25% height)"
echo "  ✅ Beautiful NEON colors"
echo "  ✅ Emoji pane titles"
echo "  ✅ Git branch in status bar"
echo "  ✅ Resize hotkeys (Ctrl+Alt+Arrows)"
echo "  ✅ Mouse support"
echo "  ✅ Sound alerts available"
echo
echo "🎨 Optional: Rich Dashboard"
echo "  Run in orchestrator pane:"
echo "  $ python3 scripts/orchestrator_dashboard.py"
echo
echo "🔊 Optional: Test Sound Alerts"
echo "  $ python3 scripts/sound_alerts.py success"
echo "  $ python3 scripts/sound_alerts.py error"
echo
echo "⌨️  Hotkeys:"
echo "  M         - Toggle PM/Implementation mode"
echo "  Ctrl+Alt+Arrows - Resize panes"
echo "  Ctrl+Shift+Arrows - Swap panes"
echo "  Ctrl+Alt+Z - Toggle zoom"
echo "  Ctrl+B, z  - Native zoom toggle"
echo
echo "📚 Documentation:"
echo "  ENHANCEMENTS_COMPLETE.md - All features"
echo "  DOPE_LAYOUT_COLORS.md - Color reference"
echo "  IMPLEMENTATION_SUMMARY.md - Full summary"
echo
echo "🚀 Attach to session:"
echo "  $ tmux attach -t dopemux"
echo
echo "╔════════════════════════════════════════╗"
echo "║     LET'S FUCKING GO! 🔥              ║"
echo "╚════════════════════════════════════════╝"
