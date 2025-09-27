#!/bin/bash
# ConPort Service Status Script
# Check ConPort MCP server health and status

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[ConPort]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[ConPort]${NC} $1"
}

log_error() {
    echo -e "${RED}[ConPort]${NC} $1"
}

log_detail() {
    echo -e "${BLUE}[ConPort]${NC} $1"
}

# Function to check if ConPort is running
check_process() {
    local pids=$(pgrep -f "conport-mcp" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "running"
        return 0
    else
        echo "stopped"
        return 1
    fi
}

# Function to check HTTP health
check_http_health() {
    local port="$1"
    if [ -z "$port" ]; then
        return 1
    fi

    local health_url="http://127.0.0.1:$port/"

    if curl -s -o /dev/null -w "%{http_code}" "$health_url" --connect-timeout 3 | grep -q "200"; then
        return 0
    else
        return 1
    fi
}

# Function to get detailed process info
get_process_info() {
    local pids=$(pgrep -f "conport-mcp" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        for pid in $pids; do
            if kill -0 "$pid" 2>/dev/null; then
                local cmd=$(ps -p "$pid" -o command= 2>/dev/null || echo "Unknown")
                local start_time=$(ps -p "$pid" -o lstart= 2>/dev/null || echo "Unknown")
                local cpu_mem=$(ps -p "$pid" -o %cpu,%mem 2>/dev/null || echo "Unknown")

                log_detail "  PID: $pid"
                log_detail "  Command: $cmd"
                log_detail "  Started: $start_time"
                log_detail "  CPU/Memory: $cpu_mem"
            fi
        done
    fi
}

# Function to show comprehensive status
show_status() {
    log_info "🔍 ConPort MCP Server Status"
    echo ""

    # Check process status
    local process_status=$(check_process)
    if [ "$process_status" = "running" ]; then
        log_info "📊 Process Status: ✅ RUNNING"
        get_process_info
    else
        log_error "📊 Process Status: ❌ STOPPED"
    fi

    echo ""

    # Check PID file
    if [ -f "$PROJECT_ROOT/.conport/conport.pid" ]; then
        local stored_pid=$(cat "$PROJECT_ROOT/.conport/conport.pid")
        if kill -0 "$stored_pid" 2>/dev/null; then
            log_info "📝 PID File: ✅ Valid (PID: $stored_pid)"
        else
            log_warn "📝 PID File: ⚠️  Stale (PID: $stored_pid not running)"
        fi
    else
        log_detail "📝 PID File: ➖ Not found"
    fi

    # Check port file and HTTP health
    if [ -f "$PROJECT_ROOT/.conport/port" ]; then
        local port=$(cat "$PROJECT_ROOT/.conport/port")
        log_info "🌐 Port: $port"

        if check_http_health "$port"; then
            log_info "🏥 HTTP Health: ✅ HEALTHY"

            # Try to get health details
            local health_response=$(curl -s "http://127.0.0.1:$port/health" 2>/dev/null || true)
            if [ -n "$health_response" ]; then
                log_detail "   Response: $health_response"
            fi
        else
            log_error "🏥 HTTP Health: ❌ UNHEALTHY"
        fi
    else
        log_detail "🌐 Port: ➖ Unknown (port file not found)"
    fi

    echo ""

    # Check data directories
    log_info "📂 Data Status:"
    if [ -d "$PROJECT_ROOT/.conport" ]; then
        log_info "   Session data: ✅ $PROJECT_ROOT/.conport/"
        if [ -d "$PROJECT_ROOT/.conport/sessions" ]; then
            local session_count=$(find "$PROJECT_ROOT/.conport/sessions" -name "*.json" 2>/dev/null | wc -l || echo "0")
            log_detail "     Sessions: $session_count files"
        fi
    else
        log_warn "   Session data: ⚠️  Directory missing"
    fi

    if [ -f "$PROJECT_ROOT/context_portal/context.db" ]; then
        local db_size=$(ls -lh "$PROJECT_ROOT/context_portal/context.db" | awk '{print $5}')
        log_info "   Database: ✅ $db_size ($PROJECT_ROOT/context_portal/context.db)"
    else
        log_warn "   Database: ⚠️  Not found"
    fi

    if [ -d "$PROJECT_ROOT/context_portal/conport_vector_data" ]; then
        log_info "   Vector data: ✅ $PROJECT_ROOT/context_portal/conport_vector_data/"
    else
        log_warn "   Vector data: ⚠️  Directory missing"
    fi

    echo ""

    # Check logs
    log_info "📋 Recent Log Activity:"
    if [ -f "$PROJECT_ROOT/.conport/logs/conport.log" ]; then
        log_info "   Main log: ✅ Available"
        local recent_lines=$(tail -3 "$PROJECT_ROOT/.conport/logs/conport.log" 2>/dev/null || echo "Unable to read log")
        log_detail "   Last 3 lines:"
        echo "$recent_lines" | while read -r line; do
            log_detail "     $line"
        done
    else
        log_detail "   Main log: ➖ Not found"
    fi

    if [ -f "$PROJECT_ROOT/.conport/logs/startup.log" ]; then
        local startup_size=$(ls -lh "$PROJECT_ROOT/.conport/logs/startup.log" 2>/dev/null | awk '{print $5}')
        log_detail "   Startup log: $startup_size"
    fi

    echo ""

    # Overall assessment
    if [ "$process_status" = "running" ] && [ -f "$PROJECT_ROOT/.conport/port" ]; then
        local port=$(cat "$PROJECT_ROOT/.conport/port")
        if check_http_health "$port"; then
            log_info "🎯 Overall Status: ✅ FULLY OPERATIONAL"
            log_info "   ConPort is ready for ADHD session memory management!"
        else
            log_warn "🎯 Overall Status: ⚠️  RUNNING BUT UNHEALTHY"
            log_warn "   Process is running but HTTP endpoint is not responding"
        fi
    elif [ "$process_status" = "running" ]; then
        log_warn "🎯 Overall Status: ⚠️  PARTIALLY RUNNING"
        log_warn "   Process found but configuration incomplete"
    else
        log_error "🎯 Overall Status: ❌ STOPPED"
        log_error "   Use 'scripts/conport/start.sh' to start the service"
    fi
}

# Function to show quick status (for use in other scripts)
quick_status() {
    local process_status=$(check_process)
    if [ "$process_status" = "running" ]; then
        if [ -f "$PROJECT_ROOT/.conport/port" ]; then
            local port=$(cat "$PROJECT_ROOT/.conport/port")
            if check_http_health "$port"; then
                echo "healthy:$port"
                return 0
            else
                echo "unhealthy:$port"
                return 1
            fi
        else
            echo "running:unknown_port"
            return 1
        fi
    else
        echo "stopped"
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            quick_status
            exit $?
            ;;
        --help)
            echo "Usage: $0 [--quick]"
            echo ""
            echo "Check ConPort MCP server status"
            echo ""
            echo "Options:"
            echo "  --quick    Show quick status only (for scripts)"
            echo "  --help     Show this help message"
            echo ""
            echo "Quick status output format:"
            echo "  healthy:PORT     - Service is running and healthy on PORT"
            echo "  unhealthy:PORT   - Service is running but not responding on PORT"
            echo "  running:unknown_port - Service is running but port unknown"
            echo "  stopped          - Service is not running"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Show full status by default
show_status