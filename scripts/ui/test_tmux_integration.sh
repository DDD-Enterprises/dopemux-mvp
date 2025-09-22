#!/bin/bash
# Test script for MetaMCP tmux integration

echo "🚀 Testing MetaMCP Tmux Integration"
echo "=================================="

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "❌ Tmux not found!"
    exit 1
fi

echo "✅ Tmux version: $(tmux -V)"

# Check if tmux config exists
if [ -f ~/.tmux.conf ]; then
    echo "✅ Tmux config found at ~/.tmux.conf"
else
    echo "❌ No tmux config found!"
    exit 1
fi

# Test status bar script directly
echo ""
echo "🎨 Testing status bar output:"
echo "----------------------------"
python /Users/hue/code/dopemux-mvp/scripts/ui/metamcp_status.py

echo ""
echo ""
echo "🔄 Testing query script:"
echo "------------------------"
python /Users/hue/code/dopemux-mvp/metamcp_simple_query.py get_status

echo ""
echo ""
echo "📊 Starting tmux session with MetaMCP status bar..."
echo "===================================================="
echo ""
echo "Instructions:"
echo "• A new tmux session will start with the MetaMCP status bar"
echo "• You'll see role, token usage, session time, and health status"
echo "• Try key bindings: C-b d (developer), C-b r (researcher), etc."
echo "• Type 'exit' or press C-b d to detach from tmux"
echo ""
echo "Press Enter to continue..."
read

# Start tmux session with MetaMCP integration
tmux new-session -d -s "metamcp-demo" \; \
     send-keys "echo 'Welcome to MetaMCP ADHD-optimized tmux!'" Enter \; \
     send-keys "echo 'Status bar shows: Role | Tokens | Time | Health | ADHD Features'" Enter \; \
     send-keys "echo 'Try switching roles with C-b + role letter (d/r/p/v/o/a/b)'" Enter \; \
     send-keys "echo 'Press C-b + B for break reminder'" Enter \; \
     send-keys "echo 'Type exit to close this demo'" Enter \; \
     attach-session -t "metamcp-demo"

echo ""
echo "🎯 Tmux integration test completed!"