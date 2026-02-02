#!/bin/bash
# ConPort Service Stop Script
# Gracefully shutdown ConPort MCP server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Function to stop ConPort gracefully
stop_conport() {
    log_info "🛑 Stopping ConPort MCP server..."

    local stopped=false

    # Try to stop using PID file first
    if [ -f "$PROJECT_ROOT/.conport/conport.pid" ]; then
        local pid=$(cat "$PROJECT_ROOT/.conport/conport.pid")

        if kill -0 "$pid" 2>/dev/null; then
            log_info "Sending SIGTERM to PID $pid..."
            kill -TERM "$pid"

            # Wait up to 10 seconds for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    log_info "✅ ConPort stopped gracefully"
                    rm -f "$PROJECT_ROOT/.conport/conport.pid"
                    stopped=true
                    break
                fi
                sleep 1
            done

            # Force kill if still running
            if ! $stopped && kill -0 "$pid" 2>/dev/null; then
                log_warn "Forcing shutdown with SIGKILL..."
                kill -KILL "$pid" 2>/dev/null || true
                rm -f "$PROJECT_ROOT/.conport/conport.pid"
                stopped=true
                log_info "✅ ConPort force stopped"
            fi
        else
            log_warn "PID file exists but process not running, cleaning up..."
            rm -f "$PROJECT_ROOT/.conport/conport.pid"
        fi
    fi

    # Fallback: kill any conport-mcp processes
    if ! $stopped; then
        local pids=$(pgrep -f "conport-mcp" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            log_info "Found running ConPort processes: $pids"
            echo $pids | xargs -r kill -TERM

            sleep 2

            # Force kill if still running
            pids=$(pgrep -f "conport-mcp" 2>/dev/null || true)
            if [ -n "$pids" ]; then
                log_warn "Force killing remaining processes..."
                echo $pids | xargs -r kill -KILL
            fi

            log_info "✅ ConPort stopped"
            stopped=true
        fi
    fi

    # Clean up runtime files
    rm -f "$PROJECT_ROOT/.conport/conport.pid"
    rm -f "$PROJECT_ROOT/.conport/port"

    if ! $stopped; then
        log_warn "⚠️  ConPort was not running"
    fi

    return 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            echo "Usage: $0"
            echo ""
            echo "Stop ConPort MCP server gracefully"
            echo ""
            echo "This script will:"
            echo "  1. Send SIGTERM for graceful shutdown"
            echo "  2. Wait up to 10 seconds"
            echo "  3. Force kill if necessary"
            echo "  4. Clean up PID and port files"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Stop the service
stop_conport