#!/bin/bash
# Dopemux PM Dashboard Script
# Manages pane-specific PM views with real-time data
# ADHD-optimized: Progressive disclosure, visual indicators, chunked information

set -euo pipefail

# Configuration
WORKSPACE_ID="/Users/hue/code/dopemux-mvp"
CONPORT_CONTAINER="mcp-conport_main"
LEANTIME_TOKEN="${LEAN_MCP_TOKEN:-}"
MAX_ITEMS=5  # ADHD: Limit items to prevent overwhelm
CACHE_TTL=30

# Colors for visual indicators
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Pane type from argument
PANE_TYPE="${1:-overview}"

# Function to query ConPort (simplified for demo)
query_conport() {
    local tool="$1"
    local args="${2:-}"

    # In production, this would make actual MCP calls
    # For now, simulate responses
    case "$tool" in
        "conport_work_upcoming_next")
            cat << 'EOF'
[
  {"id": "work/ui-001", "title": "Dark mode toggle", "priority": "high", "status": "upcoming", "cognitive_load": 3},
  {"id": "work/api-002", "title": "User authentication", "priority": "medium", "status": "upcoming", "cognitive_load": 5},
  {"id": "work/db-003", "title": "Database optimization", "priority": "low", "status": "upcoming", "cognitive_load": 7}
]
EOF
            ;;
        "conport_decisions_get")
            cat << 'EOF'
[
  {"id": "dec/001", "title": "Use React hooks over class components", "who": "ai-agent", "when_ts": "2025-11-01T10:00:00Z"},
  {"id": "dec/002", "title": "Implement optimistic updates for UX", "who": "ai-agent", "when_ts": "2025-11-01T11:00:00Z"}
]
EOF
            ;;
        "conport_work_get_progress")
            cat << 'EOF'
[
  {"id": "work/ui-001", "status": "in_progress", "description": "Implementing theme toggle"},
  {"id": "work/api-002", "status": "done", "description": "Auth endpoint completed"}
]
EOF
            ;;
        *)
            echo "[]"
            ;;
    esac
}

# Function to query Leantime (if available)
query_leantime() {
    local endpoint="$1"

    if [[ -z "$LEANTIME_TOKEN" ]]; then
        echo '{"error": "Leantime not configured"}'
        return
    fi

    # Simulate Leantime API calls
    case "$endpoint" in
        "tickets")
            cat << 'EOF'
[
  {"id": "LT-123", "title": "User onboarding flow", "status": "open", "priority": "high"},
  {"id": "LT-124", "title": "Performance monitoring", "status": "in_progress", "priority": "medium"}
]
EOF
            ;;
        "milestones")
            cat << 'EOF'
[
  {"name": "Phase 1 Complete", "progress": 85, "due_date": "2025-11-15"},
  {"name": "MVP Launch", "progress": 60, "due_date": "2025-12-01"}
]
EOF
            ;;
        *)
            echo "[]"
            ;;
    esac
}

# ADHD Progress Bar Function
progress_bar() {
    local percent="$1"
    local width=10
    local filled=$((percent * width / 100))
    local empty=$((width - filled))

    printf "["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] %d%%" "$percent"
}

# Priority Color Function
priority_color() {
    local priority="$1"
    case "$priority" in
        "critical"|"high") echo -e "${RED}$priority${NC}" ;;
        "medium") echo -e "${YELLOW}$priority${NC}" ;;
        "low") echo -e "${GREEN}$priority${NC}" ;;
        *) echo "$priority" ;;
    esac
}

# Cognitive Load Indicator
cognitive_indicator() {
    local load="$1"
    # Handle jq output that might have quotes or be null
    load=$(echo "$load" | tr -d '"' | sed 's/null/5/')  # Default to 5 if null

    # Ensure it's a valid number
    if ! [[ "$load" =~ ^[0-9]+$ ]]; then
        load=5
    fi

    if (( load <= 3 )); then
        echo -e "${GREEN}🟢 Low${NC}"
    elif (( load <= 6 )); then
        echo -e "${YELLOW}🟡 Medium${NC}"
    else
        echo -e "${RED}🔴 High${NC}"
    fi
}

# Main Dashboard Functions

show_orchestrator_dashboard() {
    echo -e "${CYAN}🎯 Dopemux Orchestration Hub${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    # Next Task Priority
    echo -e "${YELLOW}📋 Next Priority Task:${NC}"
    NEXT_TASK=$(query_conport "conport_work_upcoming_next" | jq -r '.[0].title // "No tasks available"' 2>/dev/null)
    NEXT_PRIORITY=$(query_conport "conport_work_upcoming_next" | jq -r '.[0].priority // "unknown"' 2>/dev/null)
    echo -e "  $(priority_color "$NEXT_PRIORITY"): $NEXT_TASK"
    echo

    # Sprint Progress (simulated)
    echo -e "${PURPLE}📊 Sprint Progress:${NC}"
    COMPLETED=$(query_conport "conport_work_get_progress" | jq -r '[.[] | select(.status == "done")] | length' 2>/dev/null || echo "2")
    TOTAL=$(query_conport "conport_work_upcoming_next" | jq -r 'length + 2' 2>/dev/null || echo "5")
    PROGRESS=$((COMPLETED * 100 / TOTAL))
    echo "  $(progress_bar "$PROGRESS") ($COMPLETED/$TOTAL tasks)"
    echo

    # Recent Activity
    echo -e "${GREEN}⚡ Recent Activity:${NC}"
    query_conport "conport_decisions_get" | jq -r '.[0:2][] | "  ✅ \(.title | .[0:40])..."' 2>/dev/null || echo "  No recent decisions"
}

show_conport_dashboard() {
    echo -e "${CYAN}🧠 ConPort Memory Hub${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    # Upcoming Work Items
    echo -e "${YELLOW}📋 Upcoming Work (Top $MAX_ITEMS):${NC}"
    WORK_ITEMS=$(query_conport "conport_work_upcoming_next")
    if echo "$WORK_ITEMS" | jq -e '. | length > 0' >/dev/null 2>&1; then
        # Parse each item and display
        echo "$WORK_ITEMS" | jq -r ".[:$MAX_ITEMS][] | \"  \(.priority | ascii_upcase): \(.title)\"" 2>/dev/null || echo "  Parse error in work items"
    else
        echo "  No upcoming work"
    fi
    echo

    # Recent Decisions
    echo -e "${PURPLE}🤔 Recent Decisions:${NC}"
    query_conport "conport_decisions_get" | jq -r '.[0:3][] | "  📝 \(.title | .[0:50])..."' 2>/dev/null || echo "  No recent decisions"
    echo

    # Work Status Summary
    echo -e "${GREEN}📊 Work Status:${NC}"
    TOTAL_UPCOMING=$(query_conport "conport_work_upcoming_next" | jq -r 'length' 2>/dev/null || echo "0")
    TOTAL_IN_PROGRESS=$(query_conport "conport_work_get_progress" | jq -r '[.[] | select(.status == "in_progress")] | length' 2>/dev/null || echo "1")
    TOTAL_DONE=$(query_conport "conport_work_get_progress" | jq -r '[.[] | select(.status == "done")] | length' 2>/dev/null || echo "2")

    echo "  🔄 In Progress: $TOTAL_IN_PROGRESS"
    echo "  📋 Upcoming: $TOTAL_UPCOMING"
    echo "  ✅ Completed: $TOTAL_DONE"
}

show_leantime_dashboard() {
    echo -e "${CYAN}🎯 Leantime Strategic PM${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    if [[ -z "$LEANTIME_TOKEN" ]]; then
        echo -e "${YELLOW}⚠️  Leantime not configured${NC}"
        echo "  Set LEAN_MCP_TOKEN to enable strategic PM"
        return
    fi

    # Strategic Tickets
    echo -e "${YELLOW}🎫 Strategic Tickets:${NC}"
    query_leantime "tickets" | jq -r '.[0:3][] | "  \(.status == "open" and "🔓" or "🔒") \(.title) [\(.priority)]"' 2>/dev/null || echo "  No strategic tickets"
    echo

    # Milestone Progress
    echo -e "${PURPLE}🏁 Milestone Progress:${NC}"
    query_leantime "milestones" | jq -r '.[0:2][] | "  📍 \(.name): $(progress_bar .progress)"' 2>/dev/null || echo "  No milestones defined"
    echo

    # Strategic Alignment
    echo -e "${GREEN}🎯 Strategic Alignment:${NC}"
    UPCOMING_COUNT=$(query_conport "conport_work_upcoming_next" | jq -r 'length' 2>/dev/null || echo "0")
    TICKET_COUNT=$(query_leantime "tickets" | jq -r 'length' 2>/dev/null || echo "0")
    echo "  Tactical Tasks: $UPCOMING_COUNT"
    echo "  Strategic Tickets: $TICKET_COUNT"
    echo "  Alignment: $([ "$UPCOMING_COUNT" -gt 0 ] && [ "$TICKET_COUNT" -gt 0 ] && echo "✅ Synced" || echo "⚠️  Needs sync")"
}

show_validation_dashboard() {
    echo -e "${CYAN}🧪 Playwright Validation${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    # Validation Status
    echo -e "${YELLOW}🧪 Recent Validations:${NC}"
    # In practice, this would query validation results from ConPort artifacts
    echo "  ✅ Dark mode toggle: Passed (screenshot attached)"
    echo "  ⚠️  User auth flow: Needs review (1 failure)"
    echo

    # Test Coverage
    echo -e "${PURPLE}📊 Test Coverage:${NC}"
    echo "  UI Components: $(progress_bar 75)"
    echo "  API Endpoints: $(progress_bar 60)"
    echo "  Integration Tests: $(progress_bar 40)"
    echo

    # Blockers
    echo -e "${RED}🚫 Validation Blockers:${NC}"
    echo "  None currently"
}

show_morph_dashboard() {
    echo -e "${CYAN}🔧 Morph Code Apply${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    # Recent Code Changes
    echo -e "${YELLOW}🔧 Recent Code Applications:${NC}"
    # In practice, this would show recent Morph diffs
    echo "  ✅ Applied dark mode component (5 lines changed)"
    echo "  ✅ Fixed auth validation logic (3 lines changed)"
    echo

    # Accuracy Metrics
    echo -e "${PURPLE}📊 Morph Performance:${NC}"
    echo "  Success Rate: $(progress_bar 98)"
    echo "  Average Apply Time: 2.3s"
    echo "  Lines Changed Today: 42"
    echo

    # Linked Tasks
    echo -e "${GREEN}🔗 Linked to Tasks:${NC}"
    echo "  work/ui-001: Dark mode implementation"
    echo "  work/api-002: Auth endpoint fixes"
}

show_zen_dashboard() {
    echo -e "${CYAN}🧠 Zen Reasoning Context${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    # Current Reasoning State
    echo -e "${YELLOW}🤔 Reasoning Status:${NC}"
    echo "  Active Sessions: 1"
    echo "  Consensus Mode: Available"
    echo "  Multi-Model Ready: ✅"
    echo

    # Recent Escalations
    echo -e "${PURPLE}📈 Recent Escalations:${NC}"
    echo "  Task complexity assessment (2h ago)"
    echo "  Architecture decision validation (4h ago)"
    echo

    # PM Context
    echo -e "${GREEN}🎯 PM Integration:${NC}"
    echo "  Available for complex task analysis"
    echo "  Ready for decision consensus"
    echo "  Multi-model validation enabled"
}

# Main execution based on pane type
clear
case "$PANE_TYPE" in
    "orchestrator") show_orchestrator_dashboard ;;
    "conport") show_conport_dashboard ;;
    "leantime") show_leantime_dashboard ;;
    "validation") show_validation_dashboard ;;
    "morph") show_morph_dashboard ;;
    "zen") show_zen_dashboard ;;
    *)
        echo -e "${RED}❌ Unknown pane type: $PANE_TYPE${NC}"
        echo "Available types: orchestrator, conport, leantime, validation, morph, zen"
        ;;
esac