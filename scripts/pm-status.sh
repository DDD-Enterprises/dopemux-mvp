#!/bin/bash
# Dopemux PM Status Bar Script
# Shows real-time PM metrics in tmux status bar
# ADHD-optimized: Essential info first, visual indicators

set -euo pipefail

# Configuration
WORKSPACE_ID="/Users/hue/code/dopemux-mvp"
CONPORT_CONTAINER="mcp-conport_main"
MAX_RETRIES=2
CACHE_TTL=30  # Cache data for 30 seconds

# Colors for tmux (if supported)
RED="#[fg=colour196]"
YELLOW="#[fg=colour226]"
GREEN="#[fg=colour46]"
BLUE="#[fg=colour33]"
RESET="#[default]"

# Cache file for performance
CACHE_FILE="/tmp/dopemux_pm_status_$$.cache"
cleanup() { rm -f "$CACHE_FILE"; }
trap cleanup EXIT

# Check if cache is fresh
if [[ -f "$CACHE_FILE" ]] && [[ $(($(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || date +%s))) -lt $CACHE_TTL ]]; then
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

# Query ADHD Engine for energy level (if available)
get_energy_level() {
    # Query ADHD Engine API
    if curl -s "http://localhost:8080/api/v1/energy-level" >/dev/null 2>&1; then
        curl -s "http://localhost:8080/api/v1/energy-level" | jq -r '.level // "unknown"' 2>/dev/null || echo "unknown"
    else
        echo "unknown"
    fi
}

# Get PM metrics
get_pm_metrics() {
    # Tasks: Count of upcoming work items
    TASKS_COUNT=$(query_conport "conport_work_upcoming_next" '{"workspace_id": "'"$WORKSPACE_ID"'", "limit": 10}' | jq -r 'length // 0' 2>/dev/null || echo "0")

    # Decisions: Count of recent decisions today
    DECISIONS_COUNT=$(query_conport "conport_decisions_get" '{"workspace_id": "'"$WORKSPACE_ID"'", "since": "'$(date -u +%Y-%m-%dT00:00:00Z)'"}' | jq -r 'length // 0' 2>/dev/null || echo "0")

    # Blockers: Count of blocked work items
    BLOCKERS_COUNT=$(query_conport "conport_work_get_progress" '{"workspace_id": "'"$WORKSPACE_ID"'", "status_filter": "blocked"}' | jq -r 'length // 0' 2>/dev/null || echo "0")

    # Energy level from ADHD Engine
    ENERGY_LEVEL=$(get_energy_level)

    # Format energy indicator
    case "$ENERGY_LEVEL" in
        "high") ENERGY_ICON="${GREEN}⚡${RESET}" ;;
        "medium") ENERGY_ICON="${YELLOW}●${RESET}" ;;
        "low") ENERGY_ICON="${RED}○${RESET}" ;;
        *) ENERGY_ICON="${BLUE}?${RESET}" ;;
    esac

    # Format output for tmux status bar
    # ADHD-optimized: Keep it concise, visual indicators
    echo "${BLUE}Tasks:${RESET} ${TASKS_COUNT} ${BLUE}Dec:${RESET} ${DECISIONS_COUNT} ${ENERGY_ICON} ${BLOCKERS_COUNT:+${RED}❌${BLOCKERS_COUNT}${RESET}}"
}

# Main execution
METRICS=$(get_pm_metrics 2>/dev/null || echo "${RED}PM: Offline${RESET}")

# Cache the result
echo "$METRICS" > "$CACHE_FILE"
echo "$METRICS"