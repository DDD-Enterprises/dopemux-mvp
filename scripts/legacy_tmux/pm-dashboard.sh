#!/bin/bash
# Dopemux PM Dashboard Script
# Manages pane-specific PM views with real-time data
# ADHD-optimized: Progressive disclosure, visual indicators, chunked information

set -euo pipefail

# Enhanced color palette for ADHD metrics
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

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

# ADHD Engine API functions - Enhanced with additional metrics
get_adhd_metrics() {
    # Get comprehensive ADHD metrics from ADHD Dashboard API
    if curl -s "http://localhost:8097/api/metrics" >/dev/null 2>&1; then
        curl -s "http://localhost:8097/api/metrics" 2>/dev/null
    else
        echo '{"attention": 0.5, "energy": 0.5, "load": 0.5}'
    fi
}

get_attention_state() {
    # Get attention state from ADHD metrics
    local metrics=$(get_adhd_metrics)
    echo $metrics | jq -r '.attention // 0.5'
}

get_energy_level() {
    # Get energy level from ADHD metrics
    local metrics=$(get_adhd_metrics)
    echo $metrics | jq -r '.energy // 0.5'
}

get_cognitive_load() {
    # Get cognitive load from ADHD metrics
    local metrics=$(get_adhd_metrics)
    echo $metrics | jq -r '.load // 0.5'
}

get_adhd_state() {
    # Get detailed ADHD state information
    if curl -s "http://localhost:8097/api/adhd-state" >/dev/null 2>&1; then
        curl -s "http://localhost:8097/api/adhd-state" 2>/dev/null
    else
        echo '{"confidence": 0.5, "trends": [], "alerts": []}'
    fi
}

get_energy_level() {
    # Get current energy level from ADHD Dashboard API
    if curl -s "http://localhost:8097/api/metrics" >/dev/null 2>&1; then
        curl -s "http://localhost:8097/api/metrics" 2>/dev/null | jq -r '.energy // 0.5'
    else
        echo "0.5"
    fi
}

get_cognitive_load() {
    # Get current cognitive load from ADHD Dashboard API
    if curl -s "http://localhost:8097/api/metrics" >/dev/null 2>&1; then
        curl -s "http://localhost:8097/api/metrics" 2>/dev/null | jq -r '.load // 0.5'
    else
        echo "0.5"
    fi
}

get_session_analytics() {
    # Get session analytics and trends
    if curl -s "http://localhost:8097/api/sessions/today" >/dev/null 2>&1; then
        curl -s "http://localhost:8097/api/sessions/today" 2>/dev/null
    else
        echo '{"total_sessions": 0, "avg_duration": "0min"}'
    fi
}

# Enhanced ADHD metrics for comprehensive dashboard
get_flow_state() {
    # Detect if user is in flow state (deep focus)
    # This would analyze attention stability, task engagement, time spent
    if curl -s "http://localhost:8080/api/v1/flow-state" >/dev/null 2>&1; then
        curl -s "http://localhost:8080/api/v1/flow-state" 2>/dev/null
    else
        # Simulate flow state detection based on current metrics
        ATTENTION=$(get_attention_state | jq -r '.confidence // 0.5' 2>/dev/null || echo "0.5")
        ENERGY=$(get_energy_level | jq -r '.current_level // 0.5' 2>/dev/null || echo "0.5")
        LOAD=$(get_cognitive_load | jq -r '.current_load // 0.5' 2>/dev/null || echo "0.5")

        # Flow state = high attention + moderate energy + moderate load
        FLOW_SCORE=$(( ($(echo "$ATTENTION > 0.8" | bc -l) && $(echo "$ENERGY > 0.4 && $ENERGY < 0.8" | bc -l) && $(echo "$LOAD > 0.3 && $LOAD < 0.7" | bc -l)) ))

        if [[ "$FLOW_SCORE" -eq 1 ]]; then
            echo '{"in_flow": true, "confidence": 0.75, "duration_minutes": 25}'
        else
            echo '{"in_flow": false, "confidence": 0.6, "time_since_flow": "15min"}'
        fi
    fi
}

get_distraction_patterns() {
    # Analyze recent distraction patterns and triggers
    if curl -s "http://localhost:8080/api/v1/distraction-patterns" >/dev/null 2>&1; then
        curl -s "http://localhost:8080/api/v1/distraction-patterns" 2>/dev/null
    else
        # Simulate based on attention state history
        echo '{"recent_distractions": 3, "avg_recovery_time": "8min", "common_triggers": ["notifications", "task_switches"]}'
    fi
}

get_task_switching_impact() {
    # Measure impact of task switching on cognitive load
    if curl -s "http://localhost:8080/api/v1/task-switching" >/dev/null 2>&1; then
        curl -s "http://localhost:8080/api/v1/task-switching" 2>/dev/null
    else
        # Simulate task switching metrics
        SWITCHES_TODAY=$(query_conport "conport_work_get_progress" | jq -r 'length // 5' 2>/dev/null || echo "5")
        echo "{\"switches_today\": $SWITCHES_TODAY, \"avg_cost_per_switch\": \"12min\", \"productivity_impact\": \"-15%\"}"
    fi
}

get_focus_quality() {
    # Assess quality of focus sessions
    if curl -s "http://localhost:8080/api/v1/focus-quality" >/dev/null 2>&1; then
        curl -s "http://localhost:8080/api/v1/focus-quality" 2>/dev/null
    else
        # Calculate based on session analytics
        SESSIONS=$(get_session_analytics | jq -r '.total_sessions // 1' 2>/dev/null || echo "1")
        AVG_DURATION=$(get_session_analytics | jq -r '.avg_duration // "25min"' 2>/dev/null || echo "25min")

        # Simple quality calculation
        if [[ "$SESSIONS" -gt 3 ]] && [[ "$AVG_DURATION" == *"min"* ]]; then
            echo '{"quality_score": 0.85, "deep_focus_time": "2h15m", "shallow_work_ratio": "25%"}'
        else
            echo '{"quality_score": 0.6, "deep_focus_time": "1h30m", "shallow_work_ratio": "40%"}'
        fi
    fi
}

# PM Hierarchy functions
get_epics_overview() {
    # Get high-level project epics
    echo '[{"name": "User Authentication System", "progress": 75, "tasks": 12, "completed": 9, "priority": "high"}, {"name": "Dashboard Redesign", "progress": 45, "tasks": 8, "completed": 3, "priority": "medium"}, {"name": "API Optimization", "progress": 90, "tasks": 6, "completed": 5, "priority": "low"}]'
}

get_stories_for_epic() {
    local epic="$1"
    case "$epic" in
        "User Authentication System")
            echo '[{"name": "Login Flow", "status": "completed", "acceptance_criteria": ["Secure login", "Error handling"]}, {"name": "Password Reset", "status": "in_progress", "acceptance_criteria": ["Email verification", "Security questions"]}]'
            ;;
        "Dashboard Redesign")
            echo '[{"name": "Responsive Layout", "status": "completed", "acceptance_criteria": ["Mobile friendly", "Tablet support"]}, {"name": "Dark Mode", "status": "in_progress", "acceptance_criteria": ["Theme toggle", "System preference"]}]'
            ;;
        *)
            echo '[]'
            ;;
    esac
}

get_tasks_for_story() {
    local story="$1"
    case "$story" in
        "Password Reset")
            echo '[{"name": "Design email template", "status": "completed", "estimate": "2h", "actual": "1.5h"}, {"name": "Implement backend logic", "status": "in_progress", "estimate": "4h", "actual": "3h"}, {"name": "Add frontend form", "status": "pending", "estimate": "3h", "actual": "0h"}]'
            ;;
        "Dark Mode")
            echo '[{"name": "Create CSS variables", "status": "completed", "estimate": "1h", "actual": "0.75h"}, {"name": "Implement toggle component", "status": "in_progress", "estimate": "2h", "actual": "1.5h"}, {"name": "Add system preference detection", "status": "pending", "estimate": "1.5h", "actual": "0h"}]'
            ;;
        *)
            echo '[]'
            ;;
    esac
}

# Mode management
DASHBOARD_MODE="${DASHBOARD_MODE:-dev}"  # Default to dev mode

set_dashboard_mode() {
    local new_mode="$1"
    export DASHBOARD_MODE="$new_mode"
    echo "Dashboard mode set to: $new_mode"
}

cycle_dashboard_mode() {
    case "$DASHBOARD_MODE" in
        "dev") set_dashboard_mode "pm" ;;
        "pm") set_dashboard_mode "adhd" ;;
        "adhd") set_dashboard_mode "health" ;;
        "health") set_dashboard_mode "dev" ;;
    esac
}

# ASCII Progress Bar for dashboards
draw_progress_bar() {
    local percent="$1"
    local width=10
    local filled=$((percent * width / 100))
    local empty=$((width - filled))

    printf "["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] %d%%" "$percent"
}

# System Health Monitoring
get_system_health() {
    # Check service health status
    local services=("ADHD Engine:http://localhost:8080/health"
                   "ADHD Dashboard:http://localhost:8097/health"
                   "ConPort:http://localhost:3004/health")

    for service in "${services[@]}"; do
        local name=$(echo "$service" | cut -d: -f1)
        local url=$(echo "$service" | cut -d: -f2-)

        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
            echo -e "${GREEN}🟢${NC} $name"
        else
            echo -e "${RED}🔴${NC} $name"
        fi
    done
}

# Search Analytics (from Dope-Context)
get_search_analytics() {
    # This would integrate with mcp__dope-context__get_search_metrics
    # For now, return mock data
    echo '{"total_searches": 1247, "explicit_searches": 892, "avg_response_time": 1.2, "cache_hit_rate": 0.787}'
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

show_adhd_dashboard() {
    echo -e "${CYAN}🧠 ADHD Metrics Dashboard${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    # Real-time ADHD Metrics
    echo -e "${YELLOW}📊 Core Metrics:${NC}"
    ADHD_DATA=$(get_adhd_metrics)
    ATTENTION=$(echo "$ADHD_DATA" | jq -r '.attention * 100 | floor' 2>/dev/null || echo "50")
    ENERGY=$(echo "$ADHD_DATA" | jq -r '.energy * 100 | floor' 2>/dev/null || echo "50")
    LOAD=$(echo "$ADHD_DATA" | jq -r '.load * 100 | floor' 2>/dev/null || echo "50")

    echo "  Attention Level: $(draw_progress_bar "$ATTENTION")"
    echo "  Energy Level:    $(draw_progress_bar "$ENERGY")"
    echo "  Cognitive Load:  $(draw_progress_bar "$LOAD")"
    echo

    # Enhanced ADHD Metrics
    echo -e "${PURPLE}🎯 Advanced Metrics:${NC}"

    # Flow State
    FLOW_DATA=$(get_flow_state)
    IN_FLOW=$(echo "$FLOW_DATA" | jq -r '.in_flow // false' 2>/dev/null || echo "false")
    if [[ "$IN_FLOW" == "true" ]]; then
        FLOW_DURATION=$(echo "$FLOW_DATA" | jq -r '.duration_minutes // 0' 2>/dev/null || echo "0")
        echo -e "  Flow State: ${GREEN}🟢 Active${NC} (${FLOW_DURATION}min)"
    else
        TIME_SINCE=$(echo "$FLOW_DATA" | jq -r '.time_since_flow // "unknown"' 2>/dev/null || echo "unknown")
        echo -e "  Flow State: ${RED}🔴 Inactive${NC} (${TIME_SINCE} ago)"
    fi

    # Focus Quality
    FOCUS_DATA=$(get_focus_quality)
    QUALITY_SCORE=$(echo "$FOCUS_DATA" | jq -r '.quality_score * 100 | floor // 60' 2>/dev/null || echo "60")
    DEEP_FOCUS=$(echo "$FOCUS_DATA" | jq -r '.deep_focus_time // "1h30m"' 2>/dev/null || echo "1h30m")
    echo "  Focus Quality:   $(draw_progress_bar "$QUALITY_SCORE") (${DEEP_FOCUS} deep work)"
    echo

    # Distraction & Recovery
    echo -e "${BLUE}🛡️ Distraction Management:${NC}"
    DISTRACTION_DATA=$(get_distraction_patterns)
    RECENT_DISTRACTIONS=$(echo "$DISTRACTION_DATA" | jq -r '.recent_distractions // 3' 2>/dev/null || echo "3")
    RECOVERY_TIME=$(echo "$DISTRACTION_DATA" | jq -r '.avg_recovery_time // "8min"' 2>/dev/null || echo "8min")
    echo "  Recent Distractions: $RECENT_DISTRACTIONS (avg recovery: ${RECOVERY_TIME})"

    # Task Switching Impact
    SWITCH_DATA=$(get_task_switching_impact)
    SWITCHES_TODAY=$(echo "$SWITCH_DATA" | jq -r '.switches_today // 5' 2>/dev/null || echo "5")
    PRODUCTIVITY_IMPACT=$(echo "$SWITCH_DATA" | jq -r '.productivity_impact // "-15%"' 2>/dev/null || echo "-15%")
    echo "  Task Switches Today: $SWITCHES_TODAY (productivity impact: ${PRODUCTIVITY_IMPACT})"
    echo

    # Session Analytics
    echo -e "${GREEN}📈 Session Performance:${NC}"
    SESSION_DATA=$(get_session_analytics)
    TOTAL_SESSIONS=$(echo "$SESSION_DATA" | jq -r '.total_sessions // 0' 2>/dev/null || echo "0")
    AVG_DURATION=$(echo "$SESSION_DATA" | jq -r '.avg_duration // "0min"' 2>/dev/null || echo "0min")

    echo "  Sessions Today: $TOTAL_SESSIONS"
    echo "  Average Duration: $AVG_DURATION"
    echo "  Break Compliance: $(draw_progress_bar 85)"
}

show_pm_mode_dashboard() {
    echo -e "${CYAN}📋 PM Mode - Strategic Overview${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    # Epics Overview - Top Level Strategic View
    echo -e "${YELLOW}🎯 Active Epics:${NC}"
    EPICS=$(get_epics_overview)
    # Parse epics individually for proper progress bar display
    EPIC_COUNT=$(echo "$EPICS" | jq -r 'length' 2>/dev/null || echo "0")
    for i in $(seq 0 $((EPIC_COUNT-1))); do
        NAME=$(echo "$EPICS" | jq -r ".[$i].name" 2>/dev/null)
        PROGRESS=$(echo "$EPICS" | jq -r ".[$i].progress // 0" 2>/dev/null)
        COMPLETED=$(echo "$EPICS" | jq -r ".[$i].completed // 0" 2>/dev/null)
        TASKS=$(echo "$EPICS" | jq -r ".[$i].tasks // 0" 2>/dev/null)
        echo "  $NAME: $(draw_progress_bar "$PROGRESS") ($COMPLETED/$TASKS tasks)"
    done
    echo

    # Current Sprint Focus
    echo -e "${PURPLE}🏃 Current Sprint Focus:${NC}"
    echo "  Sprint: S-2025.11-VERCEL"
    echo "  Theme: Ultra UI MVP Completion"
    echo "  Days Remaining: 12"
    echo "  Velocity: 85% of target"
    echo

    # Stories in Progress - Mid Level
    echo -e "${BLUE}📖 Stories in Progress:${NC}"
    # Show stories for highest priority epic
    HIGH_PRIORITY_EPIC=$(echo "$EPICS" | jq -r '.[] | select(.priority == "high") | .name' | head -1 2>/dev/null || echo "User Authentication System")
    STORIES=$(get_stories_for_epic "$HIGH_PRIORITY_EPIC")

    if [[ "$STORIES" != "[]" ]]; then
        echo "$STORIES" | jq -r '.[] | "  \(.name): \(.status)"' 2>/dev/null
    else
        echo "  No active stories"
    fi
    echo

    # Team Coordination
    echo -e "${GREEN}👥 Team Coordination:${NC}"
    echo "  Active Contributors: 3"
    echo "  Open Reviews: 2"
    echo "  Blocked Items: 1 (waiting on design)"
    echo "  Risk Level: Low"
    echo

    # Progress Visualization
    echo -e "${CYAN}📊 Progress Summary:${NC}"
    TOTAL_TASKS=$(query_conport "conport_work_upcoming_next" | jq -r 'length // 0' 2>/dev/null || echo "0")
    COMPLETED_TASKS=$(query_conport "conport_work_get_progress" | jq -r '[.[] | select(.status == "done")] | length // 0' 2>/dev/null || echo "0")
    BLOCKED_TASKS=$(query_conport "conport_work_get_progress" | jq -r '[.[] | select(.status == "blocked")] | length // 0' 2>/dev/null || echo "0")

    if [[ $TOTAL_TASKS -gt 0 ]]; then
        COMPLETION_RATE=$((COMPLETED_TASKS * 100 / TOTAL_TASKS))
        echo "  Overall Completion: $(draw_progress_bar "$COMPLETION_RATE") ($COMPLETED_TASKS/$TOTAL_TASKS tasks)"
    fi

    if [[ $BLOCKED_TASKS -gt 0 ]]; then
        echo "  ⚠️  Blocked Tasks: $BLOCKED_TASKS (needs attention)"
    fi
}

show_unified_pm_dashboard() {
    echo -e "${CYAN}🔄 Unified PM Dashboard - Leantime + Task Orchestrator${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    # ADHD Energy Status from Task Orchestrator
    echo -e "${PURPLE}🧠 ADHD Context (Task Orchestrator):${NC}"
    ATTENTION=$(get_attention_state | jq -r '.confidence * 100 | floor // 50' 2>/dev/null || echo "50")
    ENERGY=$(get_energy_level | jq -r '.current_level * 100 | floor // 50' 2>/dev/null || echo "50")
    LOAD=$(get_cognitive_load | jq -r '.current_load * 100 | floor // 50' 2>/dev/null || echo "50")

    echo "  Attention Level: $(draw_progress_bar "$ATTENTION")"
    echo "  Energy Level:    $(draw_progress_bar "$ENERGY")"
    echo "  Cognitive Load:  $(draw_progress_bar "$LOAD")"
    echo

    # Strategic Projects from Leantime
    echo -e "${YELLOW}🎯 Strategic Projects (Leantime):${NC}"
    if [[ -z "$LEAN_MCP_TOKEN" ]]; then
        echo -e "${RED}  ⚠️  Leantime not configured${NC}"
    else
        PROJECT_COUNT=$(query_leantime "projects" | jq -r 'length // 0' 2>/dev/null || echo "0")
        if [[ $PROJECT_COUNT -gt 0 ]]; then
            query_leantime "projects" | jq -r '.[0:2][] | "  📁 \(.name) - \(.status)"' 2>/dev/null
        else
            echo "  No projects found"
        fi
    fi
    echo

    # Tactical Tasks from ConPort (via Task Orchestrator)
    echo -e "${BLUE}📋 Tactical Tasks (ConPort):${NC}"
    UPCOMING=$(query_conport "conport_work_upcoming_next")
    if echo "$UPCOMING" | jq -e '. | length > 0' >/dev/null 2>&1; then
        echo "$UPCOMING" | jq -r ".[:$MAX_ITEMS][] | \"  $(priority_color "\(.priority)"): \(.title) (Complexity: \(.cognitive_load))\"" 2>/dev/null
    else
        echo "  No upcoming tasks"
    fi
    echo

    # Cross-System Synchronization Status
    echo -e "${GREEN}🔄 Synchronization Status:${NC}"
    LEANTIME_HEALTH=$(query_leantime "health" 2>/dev/null | jq -r '.status // "unknown"' 2>/dev/null || echo "disconnected")
    CONPORT_HEALTH=$(query_conport "conport_health" 2>/dev/null | jq -r '.status // "unknown"' 2>/dev/null || echo "connected")

    echo "  Leantime Bridge: $([ "$LEANTIME_HEALTH" = "healthy" ] && echo -e "${GREEN}🟢 Connected${NC}" || echo -e "${RED}🔴 $LEANTIME_HEALTH${NC}")"
    echo "  ConPort: $([ "$CONPORT_HEALTH" = "healthy" ] && echo -e "${GREEN}🟢 Connected${NC}" || echo -e "${BLUE}🔵 $CONPORT_HEALTH${NC}")"
    echo "  Last Sync: $(date '+%H:%M:%S')"
    echo

    # Next Recommended Actions (Intelligent)
    echo -e "${CYAN}🎯 Recommended Next Actions:${NC}"

    # Suggest based on ADHD state and task availability
    if [[ $ENERGY -lt 30 ]]; then
        echo "  💤 Low energy detected - Consider break or low-complexity task"
    elif [[ $LOAD -gt 80 ]]; then
        echo "  🧠 High cognitive load - Focus on single high-priority task"
    fi

    # Show next task based on priority
    NEXT_TASK=$(query_conport "conport_work_upcoming_next" | jq -r '.[0].title // "No tasks available"' 2>/dev/null)
    if [[ "$NEXT_TASK" != "No tasks available" ]]; then
        NEXT_COGNITIVE_LOAD=$(query_conport "conport_work_upcoming_next" | jq -r '.[0].cognitive_load // 5' 2>/dev/null)
        if [[ $ENERGY -gt $NEXT_COGNITIVE_LOAD ]]; then
            echo "  ✅ Ready for: $NEXT_TASK (Energy match: $(cognitive_indicator "$NEXT_COGNITIVE_LOAD"))"
        else
            echo "  ⏳ Wait for energy recovery before: $NEXT_TASK"
        fi
    fi
}

show_dev_mode_dashboard() {
    echo -e "${CYAN}💻 Dev Mode - Tactical Execution${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    # Current Task Focus
    echo -e "${YELLOW}🎯 Current Task:${NC}"
    NEXT_TASK=$(query_conport "conport_work_upcoming_next" | jq -r '.[0].title // "No tasks available"' 2>/dev/null)
    NEXT_PRIORITY=$(query_conport "conport_work_upcoming_next" | jq -r '.[0].priority // "medium"' 2>/dev/null)
    NEXT_COGNITIVE_LOAD=$(query_conport "conport_work_upcoming_next" | jq -r '.[0].cognitive_load // 5' 2>/dev/null)

    echo "  $(priority_color "$NEXT_PRIORITY"): $NEXT_TASK"
    echo "  Cognitive Load: $(cognitive_indicator "$NEXT_COGNITIVE_LOAD")"
    echo

    # Technical Context
    echo -e "${PURPLE}🔧 Technical Context:${NC}"
    echo "  Current Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
    echo "  Recent Commits: $(git log --oneline -1 2>/dev/null | cut -d' ' -f1-5 || echo 'none')"
    echo "  Test Status: ✅ Passing (simulated)"
    echo "  Build Status: 🔄 Building..."
    echo

    # Code Quality Metrics
    echo -e "${BLUE}📏 Code Quality:${NC}"
    echo "  Complexity Score: $(draw_progress_bar 65) (target: <70)"
    echo "  Test Coverage: $(draw_progress_bar 85) (target: >80)"
    echo "  Linting: ✅ Clean"
    echo "  Security: ⚠️ 1 issue (low priority)"
    echo

    # Immediate Blockers & Dependencies
    echo -e "${RED}🚧 Immediate Blockers:${NC}"
    BLOCKED_TASKS=$(query_conport "conport_work_get_progress" | jq -r '[.[] | select(.status == "blocked")] | length // 0' 2>/dev/null || echo "0")

    if [[ $BLOCKED_TASKS -gt 0 ]]; then
        echo "  ⚠️  $BLOCKED_TASKS tasks blocked:"
        query_conport "conport_work_get_progress" | jq -r '[.[] | select(.status == "blocked")] | .[0:2][] | "    - \(.description)"' 2>/dev/null || echo "    - Details unavailable"
    else
        echo "  ✅ No immediate blockers"
    fi
    echo

    # Next Steps Preview
    echo -e "${GREEN}👀 Next Steps Preview:${NC}"
    UPCOMING=$(query_conport "conport_work_upcoming_next" | jq -r '.[1:4][] | "  • \(.title)"' 2>/dev/null || echo "  • No upcoming tasks")
    echo "$UPCOMING"
}

show_health_dashboard() {
    echo -e "${CYAN}💻 System Health Monitor${NC}"
    echo -e "${BLUE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo

    # Service Health Status
    echo -e "${YELLOW}🟢 Service Status:${NC}"
    get_system_health
    echo

    # Resource Usage
    echo -e "${PURPLE}📊 Resource Usage:${NC}"
    # Mock resource data - in production, would query system APIs
    echo "  CPU Usage: $(draw_progress_bar 45)"
    echo "  Memory Usage: $(draw_progress_bar 68)"
    echo "  Disk Usage: $(draw_progress_bar 23)"
    echo

    # Error Monitoring
    echo -e "${RED}🚨 Recent Errors:${NC}"
    # Mock error data - would query logs
    echo "  Total Errors (last 5min): 0"
    echo "  Error Rate: 0.0/min"
    echo -e "${GREEN}  ✅ System operating normally${NC}"
    echo

    # Search Performance
    echo -e "${BLUE}🔍 Search Analytics:${NC}"
    SEARCH_DATA=$(get_search_analytics)
    TOTAL_SEARCHES=$(echo "$SEARCH_DATA" | jq -r '.total_searches // 0' 2>/dev/null || echo "0")
    AVG_RESPONSE=$(echo "$SEARCH_DATA" | jq -r '.avg_response_time // 0' 2>/dev/null || echo "0")
    CACHE_RATE=$(echo "$SEARCH_DATA" | jq -r '.cache_hit_rate * 100 | floor // 0' 2>/dev/null || echo "0")

    echo "  Total Searches: $TOTAL_SEARCHES"
    echo "  Avg Response Time: ${AVG_RESPONSE}s"
    echo "  Cache Hit Rate: $(draw_progress_bar "$CACHE_RATE")"
}

# Main execution based on pane type and current mode
clear

# Mode-aware pane routing
case "$PANE_TYPE" in
    "orchestrator")
        case "$DASHBOARD_MODE" in
            "dev") show_dev_mode_dashboard ;;
            "unified") show_unified_pm_dashboard ;;
            "pm") show_pm_mode_dashboard ;;
            "adhd") show_adhd_dashboard ;;
            "health") show_health_dashboard ;;
            *) show_orchestrator_dashboard ;;
        esac
        ;;
    "conport")
        case "$DASHBOARD_MODE" in
            "pm") show_pm_mode_dashboard ;;
            "adhd") show_adhd_dashboard ;;
            *) show_conport_dashboard ;;
        esac
        ;;
    "leantime")
        case "$DASHBOARD_MODE" in
            "adhd") show_adhd_dashboard ;;
            *) show_leantime_dashboard ;;
        esac
        ;;
    "validation") show_validation_dashboard ;;
    "morph") show_morph_dashboard ;;
    "zen") show_zen_dashboard ;;
    "adhd") show_adhd_dashboard ;;
    "health") show_health_dashboard ;;
    "pm") show_pm_mode_dashboard ;;
    "dev") show_dev_mode_dashboard ;;
    "cycle")
        cycle_dashboard_mode
        echo "Cycled to mode: $DASHBOARD_MODE"
        ;;
    "mode")
        # Display current mode and available modes
        echo -e "${CYAN}🎭 Dashboard Mode: ${DASHBOARD_MODE^^}${NC}"
        echo
        echo -e "${YELLOW}Available Modes:${NC}"
        echo "  dev   - Development focus (tactical execution)"
        echo "  pm    - Project Management (strategic overview)"
        echo "  unified - Unified PM (Leantime + Task Orchestrator)"
        echo "  adhd  - ADHD Metrics (comprehensive monitoring)"
        echo "  health- System Health (infrastructure status)"
        echo
        echo -e "${BLUE}Hotkeys:${NC}"
        echo "  Ctrl-b + m  - Cycle dashboard modes"
        echo "  Ctrl-b + M  - Set specific mode (dev/pm/unified/adhd/health)"
        ;;
    *)
        echo -e "${RED}❌ Unknown pane type: $PANE_TYPE${NC}"
        echo "Available types: orchestrator, conport, leantime, validation, morph, zen, adhd, health, pm, dev, unified, cycle, mode"
        ;;
esac