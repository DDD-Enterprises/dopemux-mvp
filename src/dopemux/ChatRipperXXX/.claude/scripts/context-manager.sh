#!/bin/bash

# MCP Context Manager Script
# Manages context usage, automatic compaction, and performance monitoring

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../mcp-config.json"
LOG_FILE="$SCRIPT_DIR/../monitoring/context-manager.log"
PID_FILE="$SCRIPT_DIR/../monitoring/context-manager.pid"

# Configuration values (fallback defaults)
CONTEXT_THRESHOLD=${CONTEXT_THRESHOLD:-0.8}
MONITOR_INTERVAL=${MONITOR_INTERVAL:-60}
CACHE_SIZE_MB=${CACHE_SIZE_MB:-512}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

get_context_usage() {
    # Get current context usage percentage from Claude Code
    # This is a placeholder - would need actual Claude Code API integration
    echo "0.45"  # Mock value for demonstration
}

check_context_threshold() {
    local usage=$(get_context_usage | sed 's/\.//')
    local threshold=$(echo "$CONTEXT_THRESHOLD * 100" | bc | sed 's/\..*//')

    if [ "$usage" -gt "$threshold" ]; then
        log "Context usage at ${usage}% - threshold exceeded (${threshold}%)"
        return 0
    fi
    return 1
}

compact_context() {
    log "Initiating context compaction..."

    # Trigger context compaction via Claude Code API
    # This is a placeholder - would need actual API call
    echo "Context compaction triggered via Claude Code API"

    # Log compaction action
    echo "$(date '+%s'),compaction_triggered,$CONTEXT_THRESHOLD" >> "$SCRIPT_DIR/../monitoring/compaction_history.csv"

    log "Context compaction completed"
}

clear_redundant_data() {
    log "Clearing redundant data from MCP servers..."

    # Clear OpenMemory cache if oversized
    if [ -d "$SCRIPT_DIR/../data" ]; then
        find "$SCRIPT_DIR/../data" -name "*.cache" -type f -mtime +7 -delete
    fi

    # Clear ConPort temporary files
    if [ -d "$SCRIPT_DIR/../temp" ]; then
        find "$SCRIPT_DIR/../temp" -type f -mtime +1 -delete
    fi

    log "Redundant data cleanup completed"
}

monitor_performance() {
    log "Performance monitoring cycle started"

    # Track MCP server response times
    local start_time=$(date +%s%3N)

    # Test OpenMemory response (placeholder)
    # curl -s "http://localhost:3001/health" > /dev/null 2>&1

    local end_time=$(date +%s%3N)
    local response_time=$((end_time - start_time))

    # Log performance metrics
    echo "$(date '+%s'),mcp_response_time,$response_time" >> "$SCRIPT_DIR/../monitoring/performance_metrics.csv"

    log "Performance monitoring cycle completed - MCP response time: ${response_time}ms"
}

warm_cache() {
    log "Warming MCP caches with common patterns..."

    # Warm OpenMemory with frequently used contexts
    # This is a placeholder - would need actual MCP server calls
    echo "OpenMemory cache warming completed"

    # Warm ConPort with recent project context
    echo "ConPort cache warming completed"

    log "Cache warming completed"
}

auto_clear() {
    if check_context_threshold; then
        log "AUTO CLEAR: Context threshold exceeded - initiating cleanup"

        # Try compaction first
        compact_context

        # If still over threshold, clear redundant data
        if check_context_threshold; then
            clear_redundant_data
        fi

        # Final check
        if check_context_threshold; then
            log "WARNING: Context still over threshold after cleanup"
            exit 1
        fi
    fi
}

show_status() {
    local usage=$(get_context_usage)
    local threshold_percent=$(echo "$CONTEXT_THRESHOLD * 100" | bc)

    echo "=== MCP Context Manager Status ==="
    echo "Current Usage: ${usage}%"
    echo "Threshold: ${threshold_percent}%"
    echo "Status: $([ "${usage%.*}" -gt "${threshold_percent%.*}" ] && echo "⚠️  HIGH" || echo "✅ NORMAL")"
    echo "Cache Size: ${CACHE_SIZE_MB}MB"
    echo "Monitor Interval: ${MONITOR_INTERVAL}s"
    echo "PID: $(cat "$PID_FILE" 2>/dev/null || echo "Not running")"
}

start_monitoring() {
    if [ -f "$PID_FILE" ]; then
        log "Monitoring already running (PID: $(cat "$PID_FILE"))"
        exit 1
    fi

    log "Starting MCP Context Manager monitoring daemon"
    echo $$ > "$PID_FILE"

    # Initial setup
    mkdir -p "$(dirname "$LOG_FILE")"

    # Warm caches on startup
    warm_cache

    # Main monitoring loop
    while true; do
        monitor_performance
        auto_clear
        sleep "$MONITOR_INTERVAL"
    done
}

stop_monitoring() {
    if [ ! -f "$PID_FILE" ]; then
        log "Monitoring not running"
        exit 1
    fi

    local pid=$(cat "$PID_FILE")
    log "Stopping MCP Context Manager (PID: $pid)"
    kill "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
    log "MCP Context Manager stopped"
}

usage() {
    cat << EOF
MCP Context Manager

USAGE: $0 [COMMAND]

COMMANDS:
  start           Start monitoring daemon
  stop            Stop monitoring daemon
  status          Show current status
  clear           Force context cleanup
  compact         Trigger context compaction
  warm            Warm MCP caches
  monitor         Run single performance check
  help            Show this help

ENVIRONMENT VARIABLES:
  CONTEXT_THRESHOLD    Context usage threshold (default: 0.8)
  MONITOR_INTERVAL     Monitoring interval in seconds (default: 60)
  CACHE_SIZE_MB        Cache size limit in MB (default: 512)

EOF
}

main() {
    case "${1:-help}" in
        start)
            start_monitoring
            ;;
        stop)
            stop_monitoring
            ;;
        status)
            show_status
            ;;
        clear)
            log "Manual context clear requested"
            auto_clear
            ;;
        compact)
            compact_context
            ;;
        warm)
            warm_cache
            ;;
        monitor)
            monitor_performance
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            echo "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"