#!/bin/bash
#
# Dopemux Orchestrator + ADHD Dashboard - Complete Tmux Layout
# =============================================================
#
# Creates a comprehensive development environment with:
#   - Top pane: ADHD Dashboard (compact, 3-5 lines)
#   - Main area: 3 panes (CLI, Logs, Monitoring)
#
# Layout:
#   ┌──────────────────────── ADHD Dashboard ────────────────────────┐
#   │ ⚡ MED ✓23m 💚95 🔥PEAK | 📋 Warnings | ✓ Tasks              │
#   ├────────────────┬────────────────┬──────────────────────────────┤
#   │                │                │                              │
#   │   Dopemux CLI  │   Service Logs │   Monitoring & Status        │
#   │                │                │                              │
#   └────────────────┴────────────────┴──────────────────────────────┘
#

set -e

SESSION_NAME="dopemux-session-manager"
WORKSPACE="/Users/hue/code/dopemux-mvp"

# Colors for output
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 Launching Dopemux Orchestrator Environment${NC}"
echo "=============================================="

# Kill existing session if it exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo -e "${YELLOW}🔄 Killing existing session: $SESSION_NAME${NC}"
    tmux kill-session -t $SESSION_NAME
fi

# Create new tmux session (detached)
echo -e "${GREEN}✓${NC} Creating tmux session: $SESSION_NAME"
tmux new-session -d -s $SESSION_NAME -n "Orchestrator" -c $WORKSPACE

# Set pane border status (show pane titles)
tmux set-option -t $SESSION_NAME pane-border-status top
tmux set-option -t $SESSION_NAME pane-border-format "#{pane_index}: #{pane_title}"

# ============================================
# STEP 1: Create top pane for ADHD Dashboard
# ============================================

echo -e "${GREEN}✓${NC} Creating ADHD Dashboard (top pane)"

# Split window horizontally to create top pane (20% height)
tmux split-window -v -p 80 -t $SESSION_NAME:0

# Move to top pane (pane 0)
tmux select-pane -t $SESSION_NAME:0.0

# Launch compact dashboard in top pane
if [ -f "$WORKSPACE/scripts/dopemux-compact-dashboard.py" ]; then
    tmux send-keys -t $SESSION_NAME:0.0 "cd $WORKSPACE" C-m
    tmux send-keys -t $SESSION_NAME:0.0 "python3 scripts/dopemux-compact-dashboard.py show --mode all" C-m
    tmux select-pane -t $SESSION_NAME:0.0 -T "🧠 ADHD Dashboard"
else
    # Fallback to simple dashboard if compact not available
    tmux send-keys -t $SESSION_NAME:0.0 "cd $WORKSPACE" C-m
    tmux send-keys -t $SESSION_NAME:0.0 "while true; do clear; echo '🧠 ADHD Dashboard'; echo '=================='; echo 'Status: ✓ Running'; echo 'Time: '\$(date +%H:%M:%S); sleep 5; done" C-m
    tmux select-pane -t $SESSION_NAME:0.0 -T "🧠 Dashboard"
fi

# ============================================
# STEP 2: Create 3-pane bottom layout
# ============================================

echo -e "${GREEN}✓${NC} Creating main workspace (3 panes)"

# Now working with bottom pane (pane 1), split it into 3 horizontal panes

# First split: Create left and right sections
tmux split-window -h -p 67 -t $SESSION_NAME:0.1

# Second split: Split the right section into two
tmux split-window -h -p 50 -t $SESSION_NAME:0.2

# Now we have 4 panes total:
#   0: Top (ADHD Dashboard)
#   1: Bottom-left (will be CLI)
#   2: Bottom-middle (will be Logs)
#   3: Bottom-right (will be Monitoring)

# ============================================
# PANE 1 (Bottom-Left): Dopemux CLI
# ============================================

echo -e "${GREEN}✓${NC} Setting up Dopemux CLI (pane 1)"

tmux select-pane -t $SESSION_NAME:0.1 -T "Dopemux CLI"
tmux send-keys -t $SESSION_NAME:0.1 "cd $WORKSPACE" C-m
tmux send-keys -t $SESSION_NAME:0.1 "clear" C-m
tmux send-keys -t $SESSION_NAME:0.1 "cat << 'EOF'
╔═══════════════════════════════════════════════╗
║        🧠 Dopemux Orchestrator CLI            ║
╚═══════════════════════════════════════════════╝

Available Commands:
  
  📊 Status & Monitoring
  ----------------------
  dopemux status           - Show all services
  dopemux list             - List instances
  docker ps                - Running containers
  
  🚀 Service Management
  ---------------------
  docker-compose up -d     - Start all services
  docker-compose logs -f   - Follow all logs
  docker-compose down      - Stop all services
  
  🧠 ADHD Engine
  --------------
  curl localhost:8095/api/v1/energy-level/hue
  curl localhost:8096/metrics
  
  📋 Task Orchestrator
  --------------------
  cd services/task-orchestrator
  python3 -m pytest        - Run tests
  
  🔧 Quick Actions
  ----------------
  make start               - Start Dopemux
  make stop                - Stop Dopemux
  make logs                - View logs
  
═══════════════════════════════════════════════

EOF
" C-m

# ============================================
# PANE 2 (Bottom-Middle): Service Logs
# ============================================

echo -e "${GREEN}✓${NC} Setting up Service Logs (pane 2)"

tmux select-pane -t $SESSION_NAME:0.2 -T "Service Logs"
tmux send-keys -t $SESSION_NAME:0.2 "cd $WORKSPACE" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo '📜 Service Logs - Waiting for services to start...'" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo ''" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo 'To view logs:'" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo '  docker-compose logs -f                    # All services'" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo '  docker-compose logs -f adhd_engine        # ADHD Engine only'" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo '  docker logs -f staging-activity-capture   # Activity Capture'" C-m
tmux send-keys -t $SESSION_NAME:0.2 "echo ''" C-m
tmux send-keys -t $SESSION_NAME:0.2 "# Ready for log commands" C-m

# ============================================
# PANE 3 (Bottom-Right): Monitoring & Status
# ============================================

echo -e "${GREEN}✓${NC} Setting up Monitoring (pane 3)"

tmux select-pane -t $SESSION_NAME:0.3 -T "Monitoring"
tmux send-keys -t $SESSION_NAME:0.3 "cd $WORKSPACE" C-m

# Launch the full 3-pane dashboard or monitoring script
if [ -f "$WORKSPACE/scripts/dopemux-dashboard.py" ]; then
    tmux send-keys -t $SESSION_NAME:0.3 "echo '📊 Launching Typer/Rich Dashboard...'" C-m
    tmux send-keys -t $SESSION_NAME:0.3 "sleep 2" C-m
    tmux send-keys -t $SESSION_NAME:0.3 "python3 scripts/dopemux-dashboard.py launch --pane system" C-m
elif [ -f "$WORKSPACE/scripts/launch-adhd-dashboard.sh" ]; then
    tmux send-keys -t $SESSION_NAME:0.3 "echo '📊 System monitoring will appear here...'" C-m
    tmux send-keys -t $SESSION_NAME:0.3 "watch -n 5 'docker ps --format \"table {{.Names}}\t{{.Status}}\"'" C-m
else
    # Fallback: Simple docker monitoring
    tmux send-keys -t $SESSION_NAME:0.3 "watch -n 5 'echo \"🐳 Docker Containers:\"; docker ps --format \"table {{.Names}}\t{{.Status}}\"'" C-m
fi

# ============================================
# Finalize & Attach
# ============================================

# Focus on CLI pane (pane 1)
tmux select-pane -t $SESSION_NAME:0.1

echo ""
echo -e "${GREEN}✅ Dopemux Orchestrator Environment Ready!${NC}"
echo ""
echo "Layout:"
echo "  ┌─────────────────── ADHD Dashboard ─────────────────┐"
echo "  │ Cognitive state + Untracked work + Active tasks    │"
echo "  ├────────────┬──────────────┬───────────────────────┤"
echo "  │ CLI        │ Service Logs │ Monitoring            │"
echo "  │ (pane 1)   │ (pane 2)     │ (pane 3)              │"
echo "  └────────────┴──────────────┴───────────────────────┘"
echo ""
echo "📝 Tmux Controls:"
echo "  Ctrl+b ←/→/↑/↓   - Navigate panes"
echo "  Ctrl+b q         - Show pane numbers"
echo "  Ctrl+b z         - Zoom current pane (toggle)"
echo "  Ctrl+b d         - Detach session"
echo "  Ctrl+b x         - Close current pane"
echo ""
echo "🚀 Quick Start:"
echo "  1. In CLI pane: docker-compose up -d"
echo "  2. In Logs pane: docker-compose logs -f"
echo "  3. Watch ADHD dashboard update in real-time"
echo ""
echo "🔗 Reattach anytime: tmux attach -t $SESSION_NAME"
echo ""

# Attach to the session
tmux attach-session -t $SESSION_NAME
