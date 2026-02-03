#!/bin/bash
# Dopemux PM Status Bar Script - Advanced ADHD-Optimized Version
# Features:
# - Context-aware prioritization (critical/urgent/important/normal modes)
# - Adaptive width detection for tmux panes
# - Progressive disclosure based on available space
# - Crisis mode for blockers, flow support for focused work
# - ADHD-optimized: Essential info first, visual indicators

set -euo pipefail

# Configuration
WORKSPACE_ID="/Users/hue/code/dopemux-mvp"
CONPORT_CONTAINER="mcp-conport_main"
MAX_RETRIES=2
CACHE_TTL=30  # Cache data for 30 seconds

# Adaptive display configuration
TMUX_WIDTH_LIMIT=${TMUX_WIDTH_LIMIT:-120}  # Allow override via environment
CONTEXT_AWARE_PRIORITY=${CONTEXT_AWARE_PRIORITY:-true}  # Enable context-aware display

# Colors - disabled (handled by tmux configuration)
RED=""
YELLOW=""
GREEN=""
BLUE=""
PURPLE=""
RESET=""

# Enhanced caching for performance optimization
CACHE_FILE="/tmp/dopemux_pm_status_$$.cache"
CONTEXT_CACHE="/tmp/dopemux_pm_context_$$.cache"
cleanup() {
    rm -f "$CACHE_FILE" "$CONTEXT_CACHE";
}
trap cleanup EXIT

# Smart caching: Different TTL for different data types
FAST_CACHE_TTL=15   # ADHD metrics change quickly
SLOW_CACHE_TTL=60   # PM metrics change less frequently

# Detect actual tmux pane width for adaptive display
detect_pane_width() {
    # Try to get tmux pane width, fallback to environment or default
    if [[ -n "${TMUX_PANE:-}" ]]; then
        tmux display-message -p "#{pane_width}" 2>/dev/null || echo "$TMUX_WIDTH_LIMIT"
    else
        echo "$TMUX_WIDTH_LIMIT"
    fi
}

# Context-aware prioritization based on ADHD state
get_context_priority() {
    local blockers="$1"
    local attention_state="$2"
    local energy_level="$3"

    # Priority levels: critical, urgent, important, normal
    if [[ $blockers -gt 0 ]]; then
        echo "critical"  # Show blockers prominently
    elif [[ "$attention_state" == *"HIGH"* ]] || [[ "$energy_level" == *"↓"* ]]; then
        echo "urgent"    # Show energy/attention help
    elif [[ "$attention_state" == *"FOCUSED"* ]] || [[ "$energy_level" == *"⚡"* ]]; then
        echo "important" # Show flow-supporting info
    else
        echo "normal"    # Standard balanced display
    fi
}

# Smart cache checking with different TTL for different data types
CACHE_AGE=$(($(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || date +%s)))
CONTEXT_AGE=$(($(date +%s) - $(stat -f %m "$CONTEXT_CACHE" 2>/dev/null || date +%s)))

# Use fast cache for ADHD metrics, slow cache for PM metrics
if [[ -f "$CACHE_FILE" ]] && [[ -f "$CONTEXT_CACHE" ]] && [[ $CACHE_AGE -lt $FAST_CACHE_TTL ]] && [[ $CONTEXT_AGE -lt $SLOW_CACHE_TTL ]]; then
    cat "$CACHE_FILE"
    exit 0
fi

# Function to query ConPort MCP
query_conport() {
    local tool="$1"
    local args="${2:-}"

    # Try to call ConPort via docker exec (assuming MCP is running)
    if docker ps | grep -q "$CONPORT_CONTAINER" 2>/dev/null; then
        # This is a simplified call - in practice, you'd use proper MCP client
        # For now, we'll simulate with direct database queries
        echo '{"status": "simulated", "count": 3}' | jq -r '.count // 0' 2>/dev/null || echo "0"
    else
        echo "0"  # Fallback when ConPort unavailable
    fi
}

# ADHD Engine integration with comprehensive metrics
get_energy_level() {
    # Enhanced energy level with trend indicators
    if curl -s "http://localhost:8080/api/v1/energy-level" >/dev/null 2>&1; then
        ENERGY_DATA=$(curl -s "http://localhost:8080/api/v1/energy-level" 2>/dev/null)
        LEVEL=$(echo "$ENERGY_DATA" | jq -r '.current_level * 100 | floor' 2>/dev/null || echo "0")
        TREND=$(echo "$ENERGY_DATA" | jq -r '.trend // "stable"' 2>/dev/null || echo "stable")

        # Format with trend indicator
        case "$TREND" in
            "increasing") TREND_ICON="↗️" ;;
            "decreasing") TREND_ICON="↘️" ;;
            "stable") TREND_ICON="→" ;;
            *) TREND_ICON="" ;;
        esac

        echo "${LEVEL}%${TREND_ICON}"
    else
        echo "unknown"
    fi
}

get_attention_state() {
    # Get attention state with confidence and distraction risk
    if curl -s "http://localhost:8080/api/v1/attention-state" >/dev/null 2>&1; then
        ATTENTION_DATA=$(curl -s "http://localhost:8080/api/v1/attention-state" 2>/dev/null)
        STATE=$(echo "$ATTENTION_DATA" | jq -r '.state // "unknown"' 2>/dev/null || echo "unknown")
        CONFIDENCE=$(echo "$ATTENTION_DATA" | jq -r '.confidence * 100 | floor' 2>/dev/null || echo "0")
        DISTRACTION=$(echo "$ATTENTION_DATA" | jq -r '.distraction_risk // "UNKNOWN"' 2>/dev/null || echo "UNKNOWN")

        # Color coding based on distraction risk
        case "$DISTRACTION" in
            "LOW") STATE_ICON="🟢" ;;
            "MEDIUM") STATE_ICON="🟡" ;;
            "HIGH") STATE_ICON="🔴" ;;
            *) STATE_ICON="⚪" ;;
        esac

        echo "${STATE}(${CONFIDENCE}%)${STATE_ICON}"
    else
        echo "unknown"
    fi
}

get_cognitive_load() {
    # Get cognitive load with capacity remaining
    if curl -s "http://localhost:8080/api/v1/cognitive-load" >/dev/null 2>&1; then
        LOAD_DATA=$(curl -s "http://localhost:8080/api/v1/cognitive-load" 2>/dev/null)
        CURRENT_LOAD=$(echo "$LOAD_DATA" | jq -r '.current_load * 100 | floor' 2>/dev/null || echo "0")
        CAPACITY=$(echo "$LOAD_DATA" | jq -r '.capacity_remaining * 100 | floor' 2>/dev/null || echo "0")

        echo "${CURRENT_LOAD}%/${CAPACITY}%"
    else
        echo "unknown"
    fi
}

get_break_status() {
    # Get break recommendation status
    if curl -s "http://localhost:8080/api/v1/break-recommendation" >/dev/null 2>&1; then
        BREAK_DATA=$(curl -s "http://localhost:8080/api/v1/break-recommendation" 2>/dev/null)
        SHOULD_BREAK=$(echo "$BREAK_DATA" | jq -r '.should_break // false' 2>/dev/null || echo "false")
        NEXT_BREAK=$(echo "$BREAK_DATA" | jq -r '.next_break_in // "unknown"' 2>/dev/null || echo "unknown")

        if [[ "$SHOULD_BREAK" == "true" ]]; then
            echo "🔔${NEXT_BREAK}"
        else
            echo "${NEXT_BREAK}"
        fi
    else
        echo "unknown"
    fi
}

# Get comprehensive PM metrics with ADHD integration
get_pm_metrics() {
    # PM Data from ConPort
    TASKS_COUNT=$(query_conport "conport_work_upcoming_next" '{"workspace_id": "'"$WORKSPACE_ID"'", "limit": 10}' | jq -r 'length // 0' 2>/dev/null || echo "0")
    DECISIONS_COUNT=$(query_conport "conport_decisions_get" '{"workspace_id": "'"$WORKSPACE_ID"'", "since": "'$(date -u +%Y-%m-%dT00:00:00Z)'"}' | jq -r 'length // 0' 2>/dev/null || echo "0")
    BLOCKERS_COUNT=$(query_conport "conport_work_get_progress" '{"workspace_id": "'"$WORKSPACE_ID"'", "status_filter": "blocked"}' | jq -r 'length // 0' 2>/dev/null || echo "0")

    # ADHD Metrics from ADHD Engine
    ATTENTION_STATE=$(get_attention_state)
    ENERGY_LEVEL=$(get_energy_level)
    COGNITIVE_LOAD=$(get_cognitive_load)
    BREAK_STATUS=$(get_break_status)

    # Format ADHD indicators with tmux colors
    if [[ "$ATTENTION_STATE" != "unknown" ]]; then
        ATTENTION_ICON="${BLUE}🧠${ATTENTION_STATE}${RESET}"
    else
        ATTENTION_ICON=""
    fi

    if [[ "$ENERGY_LEVEL" != "unknown" ]]; then
        ENERGY_ICON="${YELLOW}⚡${ENERGY_LEVEL}${RESET}"
    else
        ENERGY_ICON=""
    fi

    if [[ "$COGNITIVE_LOAD" != "unknown" ]]; then
        LOAD_ICON="${PURPLE}🧮${COGNITIVE_LOAD}${RESET}"
    else
        LOAD_ICON=""
    fi

    if [[ "$BREAK_STATUS" != "unknown" ]]; then
        BREAK_ICON="${GREEN}⏰${BREAK_STATUS}${RESET}"
    else
        BREAK_ICON=""
    fi

    # PM Metrics with colors
    PM_METRICS="${BLUE}Tasks:${RESET}${TASKS_COUNT} ${BLUE}Dec:${RESET}${DECISIONS_COUNT}"
    if [[ $BLOCKERS_COUNT -gt 0 ]]; then
        PM_METRICS="${PM_METRICS} ${RED}❌${BLOCKERS_COUNT}${RESET}"
    fi

    # ADHD Metrics with smart truncation
    ADHD_METRICS=""
    if [[ -n "$ATTENTION_ICON" ]]; then
        ADHD_METRICS="${ADHD_METRICS} ${ATTENTION_ICON}"
    fi
    if [[ -n "$ENERGY_ICON" ]]; then
        ADHD_METRICS="${ADHD_METRICS} ${ENERGY_ICON}"
    fi
    if [[ -n "$LOAD_ICON" ]]; then
        ADHD_METRICS="${ADHD_METRICS} ${LOAD_ICON}"
    fi
    if [[ -n "$BREAK_ICON" ]]; then
        ADHD_METRICS="${ADHD_METRICS} ${BREAK_ICON}"
    fi

    # Context-aware status line construction with adaptive width
    AVAILABLE_WIDTH=$(detect_pane_width)
    CONTEXT_PRIORITY=$(get_context_priority "$BLOCKERS_COUNT" "$ATTENTION_STATE" "$ENERGY_LEVEL")

    # Function to calculate visual length (excluding tmux color codes)
    visual_length() {
        local text="$1"
        # Remove tmux color codes: #[fg=colourXXX], #[default], etc.
        text=$(echo "$text" | sed 's/#\[[^]]*\]//g')
        echo ${#text}
    }

    # Adjust display based on context priority and available space
    case "$CONTEXT_PRIORITY" in
        "critical")
            # Crisis mode: Show blockers prominently, minimal other info
            if [[ $BLOCKERS_COUNT -gt 0 ]]; then
                BALANCED_METRICS="${PM_METRICS} ${RED}🚨 ${BLOCKERS_COUNT} BLOCKERS${RESET}"
            else
                BALANCED_METRICS="${PM_METRICS}"
            fi
            ;;
        "urgent")
            # Urgent help needed: Prioritize energy/attention support
            BALANCED_METRICS="${PM_METRICS}"
            [[ -n "$ENERGY_ICON" ]] && BALANCED_METRICS="${BALANCED_METRICS} ${ENERGY_ICON}"
            [[ -n "$ATTENTION_ICON" ]] && BALANCED_METRICS="${BALANCED_METRICS} ${ATTENTION_ICON}"
            ;;
        "important")
            # Flow support: Show encouraging metrics
            BALANCED_METRICS="${PM_METRICS}"
            [[ -n "$ATTENTION_ICON" ]] && BALANCED_METRICS="${BALANCED_METRICS} ${ATTENTION_ICON}"
            [[ -n "$ENERGY_ICON" ]] && BALANCED_METRICS="${BALANCED_METRICS} ${ENERGY_ICON}"
            [[ -n "$LOAD_ICON" && $(visual_length "$BALANCED_METRICS") -lt $((AVAILABLE_WIDTH - 20)) ]] && BALANCED_METRICS="${BALANCED_METRICS} ${LOAD_ICON}"
            ;;
        "normal"|*)
            # Balanced display: Progressive disclosure based on space
            BALANCED_METRICS="${PM_METRICS}"

            # Add ADHD metrics progressively if space allows
            if [[ $(visual_length "$BALANCED_METRICS") -lt $((AVAILABLE_WIDTH - 40)) ]]; then
                [[ -n "$ATTENTION_ICON" ]] && BALANCED_METRICS="${BALANCED_METRICS} ${ATTENTION_ICON}"
            fi
            if [[ $(visual_length "$BALANCED_METRICS") -lt $((AVAILABLE_WIDTH - 30)) ]]; then
                [[ -n "$ENERGY_ICON" ]] && BALANCED_METRICS="${BALANCED_METRICS} ${ENERGY_ICON}"
            fi
            if [[ $(visual_length "$BALANCED_METRICS") -lt $((AVAILABLE_WIDTH - 20)) ]]; then
                [[ -n "$LOAD_ICON" ]] && BALANCED_METRICS="${BALANCED_METRICS} ${LOAD_ICON}"
            fi
            if [[ $(visual_length "$BALANCED_METRICS") -lt $((AVAILABLE_WIDTH - 15)) ]]; then
                [[ -n "$BREAK_ICON" ]] && BALANCED_METRICS="${BALANCED_METRICS} ${BREAK_ICON}"
            fi

            # BALANCED_METRICS is set above, will be returned at end
            ;;
    esac

    # Return just the visual metrics (colors handled by tmux)
    echo "$BALANCED_METRICS"
}

# Main execution with enhanced caching and error handling
if METRICS_AND_CONTEXT=$(get_pm_metrics 2>/dev/null); then
    # Parse the combined output (metrics|blockers|attention|energy|width)
    METRICS=$(echo "$METRICS_AND_CONTEXT" | cut -d'|' -f1)
    BLOCKERS_COUNT=$(echo "$METRICS_AND_CONTEXT" | cut -d'|' -f2)
    ATTENTION_STATE=$(echo "$METRICS_AND_CONTEXT" | cut -d'|' -f3)
    ENERGY_LEVEL=$(echo "$METRICS_AND_CONTEXT" | cut -d'|' -f4)
    AVAILABLE_WIDTH=$(echo "$METRICS_AND_CONTEXT" | cut -d'|' -f5)

    # Success - cache metrics with appropriate TTL and output
    echo "$METRICS" > "$CACHE_FILE"
    echo "${BLOCKERS_COUNT}|${ATTENTION_STATE}|${ENERGY_LEVEL}|${AVAILABLE_WIDTH}" > "$CONTEXT_CACHE"

    echo "$METRICS"
else
    # Failure - provide clean fallback without verbose errors
    FALLBACK_METRICS="${RED}PM: Offline${RESET}"
    echo "$FALLBACK_METRICS" > "$CACHE_FILE"
    echo "0|unknown|unknown|80" > "$CONTEXT_CACHE"  # Fallback context
    echo "$FALLBACK_METRICS"
fi